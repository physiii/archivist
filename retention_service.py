"""Retention GC — two-phase, NAS-side.

Runs over the NAS archive (/media/mass/recording/<cam>/<YYYY-MM-DD>/).
The local SSD staging is owned by archive_service — it's not touched here.

Per-source policy (from sources.yml RetentionProfile):
  age < nas_continuous_days              → keep (continuous phase)
  nas_continuous_days ≤ age < nas_event_days
    keep iff labels ∩ keep_labels         → event-only phase
  age ≥ nas_event_days                    → delete

When a segment is deleted we also remove:
  - The segment file (mp4/ts)
  - The sidecar JSON
  - The transcript .vtt (if present alongside)
  - Associated keyframe thumbnails in the same directory
  - Milvus rows whose segment_path matches

Safety: RETENTION_DRY_RUN=true by default. Decisions are logged and published
as segment.deleted events with a `dry_run` flag either way.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import events_bus
import sources_config

logger = logging.getLogger("archivist.retention")


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


# Retention now operates on NAS. Keep the old env for back-compat.
NAS_SEGMENTS_ROOT = Path(os.getenv("ARCHIVIST_NAS_SEGMENTS_ROOT", "/media/mass/recording"))
# Retained for the Phase-6 test fixtures; not scanned in the production loop.
SEGMENTS_ROOT = Path(os.getenv("ARCHIVIST_SEGMENTS_ROOT", "/data/media_store/segments"))
KEYFRAMES_ROOT = Path(os.getenv("ARCHIVIST_KEYFRAMES_ROOT", "/data/media_store/keyframes"))
TRANSCRIPTS_ROOT = Path(os.getenv("ARCHIVIST_TRANSCRIPTS_ROOT", "/data/media_store/transcripts"))

RETENTION_ENABLED = _env_bool("RETENTION_ENABLED", True)
RETENTION_DRY_RUN = _env_bool("RETENTION_DRY_RUN", True)
RETENTION_SCAN_INTERVAL_S = _env_int("RETENTION_SCAN_INTERVAL_S", 3600)
RETENTION_MAX_DELETIONS_PER_PASS = _env_int("RETENTION_MAX_DELETIONS_PER_PASS", 500)
# Fallback for segments whose source is unknown (should not happen in practice).
FALLBACK_KEEP_LABELS = set(
    s.strip().lower()
    for s in (os.getenv("RETENTION_KEEP_LABELS") or "person,car,truck,motion,speech").split(",")
    if s.strip()
)
FALLBACK_CONTINUOUS_DAYS = float(os.getenv("RETENTION_FALLBACK_CONTINUOUS_DAYS", "30"))
FALLBACK_EVENT_DAYS = float(os.getenv("RETENTION_FALLBACK_EVENT_DAYS", "365"))
# Back-compat: if RETENTION_MIN_AGE_HOURS is set (old Phase-6 env), honor it as a floor.
RETENTION_MIN_AGE_HOURS = float(os.getenv("RETENTION_MIN_AGE_HOURS", "0"))
KEEP_SPEECH_MIN_CHARS = _env_int("RETENTION_KEEP_SPEECH_MIN_CHARS", 10)

# Legacy aliases — tests still reference these names.
KEEP_LABELS = FALLBACK_KEEP_LABELS

_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_last_pass: dict = {}


@dataclass
class _Decision:
    keep: bool
    reason: str


def _policy_for(source_id: str):
    src = sources_config.get_source(source_id)
    if src is None:
        return None
    return src.retention


def _decide(sidecar: dict, now: float) -> _Decision:
    start = float(sidecar.get("start_wall_ts") or 0.0)
    age_hours = (now - start) / 3600.0 if start > 0 else 0.0
    # Back-compat floor.
    if RETENTION_MIN_AGE_HOURS and age_hours < RETENTION_MIN_AGE_HOURS:
        return _Decision(True, f"young ({age_hours:.1f}h < {RETENTION_MIN_AGE_HOURS}h floor)")

    source_id = sidecar.get("source") or ""
    profile = _policy_for(source_id)
    if profile is not None:
        continuous_days = profile.nas_continuous_days
        event_days = profile.nas_event_days
        keep_set = {s.lower() for s in profile.keep_labels}
    else:
        continuous_days = FALLBACK_CONTINUOUS_DAYS
        event_days = FALLBACK_EVENT_DAYS
        keep_set = FALLBACK_KEEP_LABELS

    age_days = age_hours / 24.0
    if age_days < continuous_days:
        return _Decision(True, f"continuous ({age_days:.1f}d < {continuous_days:.0f}d)")
    if age_days >= event_days:
        return _Decision(False, f"past_event_window ({age_days:.1f}d ≥ {event_days:.0f}d)")

    labels = {str(x).lower() for x in (sidecar.get("labels") or [])}
    hits = labels & keep_set
    if hits:
        return _Decision(True, f"event_labels:{','.join(sorted(hits))}")
    if sidecar.get("has_speech"):
        tpath = sidecar.get("transcript_path")
        try:
            if tpath and Path(tpath).exists():
                text = Path(tpath).read_text(errors="ignore")
                if len(text.strip()) >= KEEP_SPEECH_MIN_CHARS:
                    return _Decision(True, "event_speech")
        except Exception:
            pass
    return _Decision(False, "no keep-worthy label or speech")


def _milvus_delete_by_segment(segment_path: str) -> int:
    try:
        import vision_service
        col = vision_service._milvus_collection_handle()
    except Exception:
        return 0
    if col is None:
        return 0
    try:
        expr = f'segment_path == "{segment_path}"'
        res = col.delete(expr)
        n = getattr(res, "delete_count", 0) or 0
        return int(n)
    except Exception:
        logger.exception("milvus delete for %s failed", segment_path)
        return 0


def _apply_deletion(sidecar_path: Path, sidecar: dict) -> tuple[bool, int, int]:
    bytes_freed = 0
    seg_path = sidecar.get("segment_path")
    seg_dir = None
    if seg_path:
        p = Path(seg_path)
        seg_dir = p.parent
        try:
            if p.exists():
                bytes_freed += p.stat().st_size
                p.unlink()
        except Exception:
            logger.exception("failed to unlink %s", p)
    tpath = sidecar.get("transcript_path")
    if tpath:
        p = Path(tpath)
        try:
            if p.exists():
                bytes_freed += p.stat().st_size
                p.unlink()
        except Exception:
            logger.exception("failed to unlink transcript %s", p)
    milvus_deleted = 0
    if seg_dir is not None and seg_dir.is_dir():
        # Keyframes post-archive live next to the segment. Delete those that fall in its window.
        start = float(sidecar.get("start_wall_ts") or 0.0)
        end = float(sidecar.get("end_wall_ts") or 0.0)
        for jpg in seg_dir.glob("*.jpg"):
            try:
                m = jpg.stat().st_mtime
                if start - 2 <= m <= end + 2:
                    bytes_freed += jpg.stat().st_size
                    jpg.unlink()
            except Exception:
                logger.exception("failed to unlink keyframe %s", jpg)
    if seg_path:
        milvus_deleted = _milvus_delete_by_segment(seg_path)
    try:
        if sidecar_path.exists():
            sidecar_path.unlink()
    except Exception:
        logger.exception("failed to unlink sidecar %s", sidecar_path)
    return True, bytes_freed, milvus_deleted


def run_gc_pass(dry_run: Optional[bool] = None, limit: Optional[int] = None,
                root: Optional[Path] = None) -> dict:
    """Run one retention GC pass.

    Default root is the NAS archive. Tests may pass a tmp path.
    """
    if dry_run is None:
        dry_run = RETENTION_DRY_RUN
    cap = limit if limit is not None else RETENTION_MAX_DELETIONS_PER_PASS
    scan_root = Path(root) if root is not None else NAS_SEGMENTS_ROOT
    scanned = 0
    kept = 0
    deleted = 0
    bytes_freed = 0
    milvus_rows_deleted = 0
    reasons = {"continuous": 0, "event_labels": 0, "event_speech": 0, "expired": 0, "no_keep": 0, "young": 0}
    now = time.time()
    t0 = time.time()
    if not scan_root.is_dir():
        return {"error": f"retention root missing: {scan_root}", "scanned": 0, "deleted": 0, "kept": 0}
    for sidecar_path in scan_root.rglob("*.json"):
        if _stop_event.is_set():
            break
        scanned += 1
        try:
            sidecar = json.loads(sidecar_path.read_text())
        except Exception:
            logger.exception("bad sidecar %s", sidecar_path)
            continue
        decision = _decide(sidecar, now)
        if decision.keep:
            kept += 1
            reason = decision.reason
            if reason.startswith("continuous"):
                reasons["continuous"] += 1
            elif reason.startswith("event_labels"):
                reasons["event_labels"] += 1
            elif reason.startswith("event_speech"):
                reasons["event_speech"] += 1
            elif reason.startswith("young"):
                reasons["young"] += 1
            continue
        if decision.reason.startswith("past_event_window"):
            reasons["expired"] += 1
        else:
            reasons["no_keep"] += 1
        if dry_run:
            logger.info("[dry-run] would delete %s (%s)", sidecar.get("segment_path"), decision.reason)
            events_bus.publish("segment.deleted", sidecar.get("source") or "unknown", {
                "path": sidecar.get("segment_path"),
                "sidecar_path": str(sidecar_path),
                "reason": decision.reason,
                "dry_run": True,
            })
            deleted += 1
        else:
            if deleted >= cap:
                logger.info("retention cap reached (%d); stopping pass", cap)
                break
            ok, freed, mvd = _apply_deletion(sidecar_path, sidecar)
            if ok:
                deleted += 1
                bytes_freed += freed
                milvus_rows_deleted += mvd
                events_bus.publish("segment.deleted", sidecar.get("source") or "unknown", {
                    "path": sidecar.get("segment_path"),
                    "sidecar_path": str(sidecar_path),
                    "reason": decision.reason,
                    "bytes_freed": freed,
                    "milvus_rows_deleted": mvd,
                    "dry_run": False,
                })
    summary = {
        "root": str(scan_root),
        "scanned": scanned,
        "kept": kept,
        "deleted": deleted,
        "bytes_freed": bytes_freed,
        "milvus_rows_deleted": milvus_rows_deleted,
        "reasons": reasons,
        "dry_run": dry_run,
        "elapsed_s": round(time.time() - t0, 2),
        "finished_at": now,
    }
    logger.info("retention pass done: %s", summary)
    global _last_pass
    _last_pass = summary
    return summary


def _scheduler_loop():
    if _stop_event.wait(120):
        return
    while not _stop_event.is_set():
        try:
            run_gc_pass()
        except Exception:
            logger.exception("retention pass failed (non-fatal)")
        if _stop_event.wait(RETENTION_SCAN_INTERVAL_S):
            return


def start() -> None:
    global _thread
    if not RETENTION_ENABLED:
        logger.info("RETENTION_ENABLED=false; skipping retention service")
        return
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_scheduler_loop, daemon=True, name="retention-gc")
    _thread.start()
    logger.info(
        "retention GC scheduled: root=%s interval=%ds dry_run=%s",
        NAS_SEGMENTS_ROOT, RETENTION_SCAN_INTERVAL_S, RETENTION_DRY_RUN,
    )


def stop(timeout: float = 5.0) -> None:
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=timeout)


def status() -> dict:
    return {
        "enabled": RETENTION_ENABLED,
        "dry_run": RETENTION_DRY_RUN,
        "nas_root": str(NAS_SEGMENTS_ROOT),
        "scan_interval_s": RETENTION_SCAN_INTERVAL_S,
        "fallback_keep_labels": sorted(FALLBACK_KEEP_LABELS),
        "fallback_continuous_days": FALLBACK_CONTINUOUS_DAYS,
        "fallback_event_days": FALLBACK_EVENT_DAYS,
        "keep_speech_min_chars": KEEP_SPEECH_MIN_CHARS,
        "alive": bool(_thread and _thread.is_alive()),
        "last_pass": _last_pass,
    }

