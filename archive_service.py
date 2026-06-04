"""Archive service — two-tier storage lifecycle.

Flow:
  0 .. local_hold_hours   — segment sits on local SSD (/data/media_store/segments)
  after local_hold_hours  — mover thread relocates segment + sidecar + keyframes
                            to NAS (/media/mass/recording/<YYYY>/<MM>/<DD>/<cam>/)

On move:
  - copy files first, verify size matches, then unlink locals (atomic-ish)
  - rewrite sidecar JSON's segment_path to the new NAS location
  - rewrite Milvus CLIP rows' segment_path so searches still resolve
  - publish segment.archived event

Default hold + destination come from each source's RetentionProfile.
All-sources backfill mode ignores hold time for a one-shot migration.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import events_bus
import sources_config

logger = logging.getLogger("archivist.archive")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


LOCAL_SEGMENTS_ROOT = Path(os.getenv("ARCHIVIST_SEGMENTS_ROOT", "/data/media_store/segments"))
LOCAL_KEYFRAMES_ROOT = Path(os.getenv("ARCHIVIST_KEYFRAMES_ROOT", "/data/media_store/keyframes"))
NAS_SEGMENTS_ROOT = Path(os.getenv("ARCHIVIST_NAS_SEGMENTS_ROOT", "/media/mass/recording"))

ARCHIVE_ENABLED = _env_bool("ARCHIVE_ENABLED", True)
ARCHIVE_SCAN_INTERVAL_S = _env_int("ARCHIVE_SCAN_INTERVAL_S", 300)   # 5 min
ARCHIVE_MAX_MOVES_PER_PASS = _env_int("ARCHIVE_MAX_MOVES_PER_PASS", 2000)
ARCHIVE_PARALLEL_WORKERS = max(1, _env_int("ARCHIVE_PARALLEL_WORKERS", 4))
ARCHIVE_MILVUS_BATCH = max(1, _env_int("ARCHIVE_MILVUS_BATCH", 128))

_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_last_pass: dict = {}
_state_lock = threading.Lock()


@dataclass
class _MoveResult:
    segment_path: str
    new_segment_path: str
    bytes_moved: int
    milvus_rows_updated: int


def _dest_for(source_id: str, seg_name: str, year: str, month: str, day: str) -> Path:
    return NAS_SEGMENTS_ROOT / year / month / day / source_id / seg_name


def _copy_verify_unlink(src: Path, dst: Path) -> int:
    """Copy src → dst, verify sizes match, unlink src. Returns bytes moved."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_size = src.stat().st_size
    tmp_dst = dst.with_suffix(dst.suffix + ".partial")
    shutil.copy2(src, tmp_dst)
    dst_size = tmp_dst.stat().st_size
    if dst_size != src_size:
        tmp_dst.unlink(missing_ok=True)
        raise RuntimeError(f"size mismatch copying {src} → {dst}: src={src_size} dst={dst_size}")
    tmp_dst.rename(dst)
    src.unlink()
    return src_size


def _milvus_rewrite_segment_path(old_path: str, new_path: str) -> int:
    """Rewrite a single segment's Milvus rows. Kept for unit-test compatibility;
    production backfill uses _milvus_rewrite_batch below."""
    return _milvus_rewrite_batch({old_path: new_path})


def _milvus_rewrite_batch(pairs: dict[str, str]) -> int:
    """Bulk-rewrite Milvus CLIP rows. Accepts {old_segment_path: new_segment_path}.

    Avoids per-segment query overhead by batching the old_path IN-list per chunk,
    keeping the insert data grouped by new_path, and flushing once at the end.
    """
    if not pairs:
        return 0
    try:
        import vision_service
        col = vision_service._milvus_collection_handle()
    except Exception:
        return 0
    if col is None:
        return 0
    total = 0
    old_paths = list(pairs.keys())
    # Chunk the IN-list to keep expressions within sane size
    for i in range(0, len(old_paths), ARCHIVE_MILVUS_BATCH):
        chunk = old_paths[i : i + ARCHIVE_MILVUS_BATCH]
        quoted = ", ".join('"' + p.replace('"', '\\"') + '"' for p in chunk)
        expr = f"segment_path in [{quoted}]"
        try:
            rows = col.query(
                expr=expr,
                output_fields=["id", "source", "wall_ts", "keyframe_path", "segment_path", "vector"],
                limit=8192,
            )
        except Exception:
            logger.exception("milvus batch query failed (%d paths)", len(chunk))
            continue
        if not rows:
            continue
        # Re-assemble per-column insert data for the batch
        sources, wall_ts, kf_paths, seg_paths, vectors = [], [], [], [], []
        for r in rows:
            old = str(r.get("segment_path") or "")
            new = pairs.get(old, old)
            sources.append(r.get("source") or "")
            wall_ts.append(float(r.get("wall_ts") or 0.0))
            kf_paths.append(str(r.get("keyframe_path") or ""))
            seg_paths.append(new)
            vectors.append(r.get("vector"))
        try:
            col.insert([sources, wall_ts, kf_paths, seg_paths, vectors])
            col.delete(expr)
            total += len(rows)
        except Exception:
            logger.exception("milvus batch insert/delete failed (%d rows)", len(rows))
    try:
        col.flush()
    except Exception:
        pass
    return total


def _move_one(sidecar_path: Path, source_id: str, keep_keyframes: bool = True) -> Optional[_MoveResult]:
    """Move a single segment + sidecar + keyframes to NAS. Returns None on failure."""
    try:
        sidecar = json.loads(sidecar_path.read_text())
    except Exception:
        logger.exception("bad sidecar %s", sidecar_path)
        return None
    old_seg = sidecar.get("segment_path")
    if not old_seg:
        return None
    old_seg_path = Path(old_seg)
    if not old_seg_path.exists():
        # Stale sidecar; clean up
        sidecar_path.unlink(missing_ok=True)
        return None

    # Derive destination y/m/d from the sidecar's start_wall_ts so we stay in UTC.
    from datetime import datetime, timezone
    start = float(sidecar.get("start_wall_ts") or 0.0) or time.time()
    _dt = datetime.fromtimestamp(start, tz=timezone.utc)
    year, month, day = _dt.strftime("%Y"), _dt.strftime("%m"), _dt.strftime("%d")
    new_seg_path = _dest_for(source_id, old_seg_path.name, year, month, day)
    new_sidecar_path = new_seg_path.with_suffix(".json")

    bytes_moved = 0
    try:
        bytes_moved += _copy_verify_unlink(old_seg_path, new_seg_path)
    except Exception:
        logger.exception("failed to move segment %s → %s", old_seg_path, new_seg_path)
        return None

    # Move transcript sidecar if any (transcripts not yet written by streaming service,
    # but handle the path for forward-compat).
    tpath = sidecar.get("transcript_path")
    new_tpath = None
    if tpath:
        tp = Path(tpath)
        if tp.exists():
            try:
                new_tp = new_seg_path.with_suffix(".vtt")
                bytes_moved += _copy_verify_unlink(tp, new_tp)
                new_tpath = str(new_tp)
            except Exception:
                logger.exception("failed to move transcript %s", tp)

    # Move keyframes that fall inside this segment's wall window.
    new_keyframe_paths: list[str] = []
    moved_kf_map: dict[str, str] = {}
    if keep_keyframes:
        end = float(sidecar.get("end_wall_ts") or 0.0)
        if start > 0 and end > start:
            kf_dt = datetime.fromtimestamp(start, tz=timezone.utc)
            kf_day = kf_dt.strftime("%Y-%m-%d")
            local_day_dir = LOCAL_KEYFRAMES_ROOT / source_id / kf_day
            nas_day_dir = NAS_SEGMENTS_ROOT / kf_dt.strftime("%Y") / kf_dt.strftime("%m") / kf_dt.strftime("%d") / source_id
            if local_day_dir.is_dir():
                for jpg in local_day_dir.glob("*.jpg"):
                    try:
                        m = jpg.stat().st_mtime
                        if start - 2 <= m <= end + 2:
                            nas_jpg = nas_day_dir / jpg.name
                            bytes_moved += _copy_verify_unlink(jpg, nas_jpg)
                            new_keyframe_paths.append(str(nas_jpg))
                            moved_kf_map[str(jpg)] = str(nas_jpg)
                    except Exception:
                        logger.exception("failed to move keyframe %s", jpg)

    # Rewrite sidecar JSON with NAS paths, then move it last.
    sidecar["segment_path"] = str(new_seg_path)
    if new_tpath:
        sidecar["transcript_path"] = new_tpath
    sidecar["archived_wall_ts"] = time.time()
    sidecar["archived_to"] = "nas"
    try:
        new_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        new_sidecar_path.write_text(json.dumps(sidecar, indent=2))
        sidecar_path.unlink(missing_ok=True)
    except Exception:
        logger.exception("failed to write new sidecar %s", new_sidecar_path)

    # Caller (run_archive_pass) batches Milvus rewrites and event publishing.
    return _MoveResult(str(old_seg_path), str(new_seg_path), bytes_moved, 0)


def run_archive_pass(
    backfill: bool = False,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> dict:
    """Sweep local segments and archive those past local_hold_hours.

    Two-phase for performance:
      Phase 1 — file moves in parallel (ThreadPoolExecutor, ARCHIVE_PARALLEL_WORKERS).
      Phase 2 — ONE batched Milvus rewrite covering every moved segment.
    Segment.archived events fire after the Milvus rewrite so consumers see
    self-consistent paths.

    backfill=True ignores the hold window — moves everything local right now.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    start_ts = time.time()
    cap = limit if limit is not None else ARCHIVE_MAX_MOVES_PER_PASS
    scanned = 0
    skipped_young = 0

    srcs = {s.id: s for s in sources_config.load_sources().values()}
    if not LOCAL_SEGMENTS_ROOT.is_dir():
        return {"error": f"local segments root missing: {LOCAL_SEGMENTS_ROOT}"}

    # --- Phase 0: enumerate eligible sidecars -----------------------------
    candidates: list[tuple[Path, str]] = []
    for sidecar_path in LOCAL_SEGMENTS_ROOT.rglob("*.json"):
        if _stop_event.is_set() or len(candidates) >= cap:
            break
        scanned += 1
        try:
            sidecar = json.loads(sidecar_path.read_text())
        except Exception:
            continue
        if sidecar.get("archived_to") == "nas":
            continue
        try:
            source_id = sidecar_path.parent.parent.name
        except Exception:
            source_id = sidecar.get("source") or "unknown"
        src = srcs.get(source_id)
        hold_hours = src.retention.local_hold_hours if src else 48.0
        end = float(sidecar.get("end_wall_ts") or 0.0)
        age_hours = (start_ts - end) / 3600.0 if end > 0 else 0.0
        if not backfill and age_hours < hold_hours:
            skipped_young += 1
            continue
        candidates.append((sidecar_path, source_id))

    if dry_run:
        summary = {
            "scanned": scanned, "moved": len(candidates), "skipped_young": skipped_young,
            "failed": 0, "bytes_moved": 0, "milvus_rows_updated": 0,
            "backfill": backfill, "dry_run": True,
            "elapsed_s": round(time.time() - start_ts, 2), "finished_at": start_ts,
        }
        with _state_lock:
            global _last_pass
            _last_pass = summary
        return summary

    # --- Phase 1: parallel file moves -------------------------------------
    results: list[_MoveResult] = []
    failed = 0
    bytes_moved = 0
    with ThreadPoolExecutor(max_workers=ARCHIVE_PARALLEL_WORKERS) as ex:
        futures = [ex.submit(_move_one, sp, sid) for sp, sid in candidates]
        for f in as_completed(futures):
            if _stop_event.is_set():
                break
            try:
                r = f.result()
            except Exception:
                logger.exception("move worker failed")
                r = None
            if r is None:
                failed += 1
            else:
                results.append(r)
                bytes_moved += r.bytes_moved

    # --- Phase 2: one bulk Milvus rewrite ---------------------------------
    pairs = {r.segment_path: r.new_segment_path for r in results}
    milvus_rows = 0
    try:
        if pairs:
            milvus_rows = _milvus_rewrite_batch(pairs)
    except Exception:
        logger.exception("milvus batch rewrite failed")

    # --- Phase 3: publish events ------------------------------------------
    for r in results:
        # Best effort — source id inferred from the new path
        try:
            src_id = Path(r.new_segment_path).parent.parent.name
        except Exception:
            src_id = "unknown"
        events_bus.publish(
            "segment.archived", src_id,
            {
                "old_path": r.segment_path,
                "new_path": r.new_segment_path,
                "bytes_moved": r.bytes_moved,
            },
        )

    summary = {
        "scanned": scanned,
        "moved": len(results),
        "skipped_young": skipped_young,
        "failed": failed,
        "bytes_moved": bytes_moved,
        "milvus_rows_updated": milvus_rows,
        "parallel_workers": ARCHIVE_PARALLEL_WORKERS,
        "backfill": backfill,
        "dry_run": False,
        "elapsed_s": round(time.time() - start_ts, 2),
        "finished_at": start_ts,
    }
    with _state_lock:
        _last_pass = summary
    logger.info("archive pass done: %s", summary)
    return summary


def _scheduler_loop():
    # Brief initial delay to let ingest stabilize.
    if _stop_event.wait(180):
        return
    while not _stop_event.is_set():
        try:
            run_archive_pass(backfill=False, dry_run=False)
        except Exception:
            logger.exception("archive pass failed (non-fatal)")
        if _stop_event.wait(ARCHIVE_SCAN_INTERVAL_S):
            return


def start() -> None:
    global _thread
    if not ARCHIVE_ENABLED:
        logger.info("ARCHIVE_ENABLED=false; skipping archive service")
        return
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_scheduler_loop, daemon=True, name="archive-mover")
    _thread.start()
    logger.info(
        "archive service scheduled: interval=%ds local→NAS=%s→%s",
        ARCHIVE_SCAN_INTERVAL_S, LOCAL_SEGMENTS_ROOT, NAS_SEGMENTS_ROOT,
    )


def stop(timeout: float = 5.0) -> None:
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=timeout)


def status() -> dict:
    return {
        "enabled": ARCHIVE_ENABLED,
        "local_root": str(LOCAL_SEGMENTS_ROOT),
        "nas_root": str(NAS_SEGMENTS_ROOT),
        "scan_interval_s": ARCHIVE_SCAN_INTERVAL_S,
        "alive": bool(_thread and _thread.is_alive()),
        "last_pass": _last_pass,
    }
