#!/usr/bin/env python3
"""Migrate /mass/recording/ from legacy layouts to /YYYY/MM/DD/{source}/{HHMMSS}.{ext}.

Runs on megamind (where /mass/recording is a local ZFS mount) so renames are
metadata-only and millions of files move in minutes, not hours.

Three populations:
  A. archivist-era: /mass/recording/{source}/{YYYY-MM-DD}/{HHMMSS}.{mp4,json,vtt,jpg}
     → /mass/recording/{YYYY}/{MM}/{DD}/{source}/{HHMMSS}.{ext}
     Sidecar JSONs have segment_path / transcript_path rewritten in-place.
     Emits mapping to --map-out for later Milvus update on sonic.
  B. Frigate-era: /mass/recording/{YYYY-MM-DD}/{HH}/{source}/{MM.SS}.mp4
     → /mass/recording/{YYYY}/{MM}/{DD}/{source}/{HH}{MM}{SS}.mp4
     No sidecars, no Milvus refs.
  C. UUID-keyed historical dirs (37425b83-..., etc.): LEFT UNTOUCHED.

Safety:
  - Idempotent: if destination exists, skip source (resumable across kills)
  - Cross-rename: os.rename within same filesystem; falls back to copy+unlink otherwise
  - Dry-run: reports without moving
  - Lock file at /mass/.archivist_migration.lock to prevent concurrent runs
  - Sidecar rewrite uses /media/mass/recording paths (what archivist sees),
    NOT /mass/recording (what megamind sees) — keeps sidecars valid inside container

Usage on megamind:
  python3 /tmp/migrate_nas_layout_2026.py --dry-run
  python3 /tmp/migrate_nas_layout_2026.py --map-out /tmp/migration_map.jsonl

Usage on sonic (after migration, updates Milvus):
  python3 /tmp/migrate_nas_layout_2026.py --apply-milvus --map-in /tmp/migration_map.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from pathlib import Path

logger = logging.getLogger("migrate_nas")

# Paths
MEGAMIND_ROOT = Path("/mass/recording")          # on megamind, local FS
CONTAINER_ROOT_STR = "/media/mass/recording"     # how archivist sees it (in sidecars)
LOCK_PATH = Path("/mass/.archivist_migration.lock")

# Known archivist camera sources — top-level dirs in archivist-era layout
ARCHIVIST_SOURCES = {
    "office", "kids", "backyard", "hallway", "front_door",
    "floodlight", "office_mic", "screens",
}

DATE_DIR_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")     # 2026-04-26
HOUR_DIR_RE = re.compile(r"^(\d{2})$")                      # 00..23
FRIGATE_FILE_RE = re.compile(r"^(\d{2})\.(\d{2})\.mp4$")    # MM.SS.mp4
YEAR_DIR_RE = re.compile(r"^(19|20)\d{2}$")                 # 1969, 2026 — skip if already new layout


# -------------------- helpers ----------------------------------------------

def _acquire_lock(dry_run: bool) -> None:
    if dry_run:
        return
    if LOCK_PATH.exists():
        pid = LOCK_PATH.read_text().strip()
        logger.error("lock file exists: %s (pid=%s). Remove it if stale.", LOCK_PATH, pid)
        sys.exit(2)
    LOCK_PATH.write_text(f"{os.getpid()}\n")


def _release_lock() -> None:
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def _safe_rename(src: Path, dst: Path) -> int:
    """Rename src → dst on same filesystem; fallback to copy+unlink across FS.
    Returns bytes moved (0 if metadata-only rename)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.rename(src, dst)
        return 0  # metadata only
    except OSError as e:
        # EXDEV = cross-device link — copy then delete
        if e.errno != 18:
            raise
        size = src.stat().st_size
        tmp = dst.with_suffix(dst.suffix + ".partial")
        shutil.copy2(src, tmp)
        if tmp.stat().st_size != size:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"size mismatch {src} -> {dst}")
        tmp.rename(dst)
        src.unlink()
        return size


def _rewrite_sidecar_paths(sidecar_path: Path, old_nas_prefix: str, new_nas_prefix: str,
                           old_source_dir: str, new_source_dir: str) -> bool:
    """Rewrite segment_path / transcript_path inside a sidecar JSON.

    old_nas_prefix / new_nas_prefix are the CONTAINER paths (/media/mass/recording/...).
    Returns True if rewritten, False on parse error.
    """
    try:
        data = json.loads(sidecar_path.read_text())
    except Exception:
        logger.exception("bad sidecar %s", sidecar_path)
        return False
    changed = False
    for key in ("segment_path", "transcript_path"):
        val = data.get(key)
        if not val or not isinstance(val, str):
            continue
        if val.startswith(old_source_dir):
            data[key] = val.replace(old_source_dir, new_source_dir, 1)
            changed = True
    if changed:
        data["migrated_layout_wall_ts"] = time.time()
        sidecar_path.write_text(json.dumps(data, indent=2))
    return True


# -------------------- archivist-era ---------------------------------------

def migrate_archivist(dry_run: bool, map_out, stats: dict) -> None:
    """Move {source}/{YYYY-MM-DD}/... → {YYYY}/{MM}/{DD}/{source}/... for each archivist source."""
    for source in sorted(ARCHIVIST_SOURCES):
        src_root = MEGAMIND_ROOT / source
        if not src_root.is_dir():
            continue
        logger.info("[archivist] scanning %s", src_root)
        for day_dir in sorted(src_root.iterdir()):
            if not day_dir.is_dir():
                continue
            m = DATE_DIR_RE.match(day_dir.name)
            if not m:
                logger.warning("unexpected entry under %s: %s (skip)", src_root, day_dir.name)
                continue
            y, mo, d = m.groups()
            dest_dir = MEGAMIND_ROOT / y / mo / d / source
            for f in sorted(day_dir.iterdir()):
                if not f.is_file():
                    continue
                dst = dest_dir / f.name
                if dst.exists():
                    stats["skipped_existing"] += 1
                    continue
                old_container = f"{CONTAINER_ROOT_STR}/{source}/{day_dir.name}/{f.name}"
                new_container = f"{CONTAINER_ROOT_STR}/{y}/{mo}/{d}/{source}/{f.name}"
                if dry_run:
                    stats["planned"] += 1
                    if stats["planned"] <= 20:
                        logger.info("[dry] %s -> %s", f, dst)
                    continue
                try:
                    bytes_moved = _safe_rename(f, dst)
                except Exception:
                    logger.exception("failed %s -> %s", f, dst)
                    stats["failed"] += 1
                    continue
                stats["moved"] += 1
                stats["bytes"] += bytes_moved
                if f.suffix == ".json":
                    old_src_dir = f"{CONTAINER_ROOT_STR}/{source}/{day_dir.name}"
                    new_src_dir = f"{CONTAINER_ROOT_STR}/{y}/{mo}/{d}/{source}"
                    _rewrite_sidecar_paths(dst, CONTAINER_ROOT_STR, CONTAINER_ROOT_STR,
                                          old_src_dir, new_src_dir)
                if f.suffix == ".mp4" and map_out is not None:
                    # Emit mapping for Milvus update phase (segment_path rewrites).
                    map_out.write(json.dumps({
                        "kind": "archivist",
                        "old": old_container,
                        "new": new_container,
                    }) + "\n")
            # Remove empty day dir
            try:
                day_dir.rmdir()
            except OSError:
                pass
        # Remove empty source root
        try:
            src_root.rmdir()
        except OSError:
            pass


# -------------------- Frigate-era -----------------------------------------

def migrate_frigate(dry_run: bool, stats: dict) -> None:
    """Move {YYYY-MM-DD}/{HH}/{source}/{MM.SS}.mp4 → {YYYY}/{MM}/{DD}/{source}/{HHMMSS}.mp4."""
    for date_dir in sorted(MEGAMIND_ROOT.iterdir()):
        if not date_dir.is_dir():
            continue
        m = DATE_DIR_RE.match(date_dir.name)
        if not m:
            continue  # skip UUIDs, year dirs, sources, etc.
        y, mo, d = m.groups()
        logger.info("[frigate] scanning %s", date_dir)
        for hour_dir in sorted(date_dir.iterdir()):
            if not hour_dir.is_dir():
                continue
            hm = HOUR_DIR_RE.match(hour_dir.name)
            if not hm:
                logger.warning("unexpected in %s: %s", date_dir, hour_dir.name)
                continue
            hh = hm.group(1)
            for source_dir in sorted(hour_dir.iterdir()):
                if not source_dir.is_dir():
                    continue
                source = source_dir.name
                dest_dir = MEGAMIND_ROOT / y / mo / d / source
                for f in sorted(source_dir.iterdir()):
                    if not f.is_file():
                        continue
                    fm = FRIGATE_FILE_RE.match(f.name)
                    if not fm:
                        # Keep unrecognized files where they are — log them
                        logger.warning("unparseable frigate file: %s", f)
                        stats["skipped_unparsed"] += 1
                        continue
                    mm, ss = fm.groups()
                    dst = dest_dir / f"{hh}{mm}{ss}.mp4"
                    if dst.exists():
                        stats["skipped_existing"] += 1
                        continue
                    if dry_run:
                        stats["planned"] += 1
                        if stats["planned"] <= 20:
                            logger.info("[dry] %s -> %s", f, dst)
                        continue
                    try:
                        bytes_moved = _safe_rename(f, dst)
                    except Exception:
                        logger.exception("failed %s -> %s", f, dst)
                        stats["failed"] += 1
                        continue
                    stats["moved"] += 1
                    stats["bytes"] += bytes_moved
                try:
                    source_dir.rmdir()
                except OSError:
                    pass
            try:
                hour_dir.rmdir()
            except OSError:
                pass
        try:
            date_dir.rmdir()
        except OSError:
            pass


# -------------------- Milvus phase (runs on sonic) ------------------------

def apply_milvus(map_path: Path) -> None:
    """Read mapping file, rewrite Milvus clip_embeddings rows' segment_path."""
    sys.path.insert(0, "/home/andy/archivist")
    try:
        import archive_service
    except Exception:
        logger.exception("cannot import archive_service")
        sys.exit(3)
    pairs: dict[str, str] = {}
    with map_path.open() as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("kind") != "archivist":
                continue
            pairs[row["old"]] = row["new"]
    logger.info("milvus: rewriting %d segment_path pairs", len(pairs))
    if not pairs:
        return
    updated = archive_service._milvus_rewrite_batch(pairs)
    logger.info("milvus: %d rows updated", updated)


# -------------------- main -------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--map-out", type=Path, default=None,
                    help="Write old→new mapping (jsonl) for later Milvus update")
    ap.add_argument("--map-in", type=Path, default=None,
                    help="Read mapping and apply Milvus rewrites (use with --apply-milvus)")
    ap.add_argument("--apply-milvus", action="store_true",
                    help="Apply Milvus segment_path rewrites from --map-in (run on sonic, not megamind)")
    ap.add_argument("--skip-archivist", action="store_true")
    ap.add_argument("--skip-frigate", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.apply_milvus:
        if not args.map_in or not args.map_in.is_file():
            logger.error("--apply-milvus requires --map-in <path>")
            return 2
        apply_milvus(args.map_in)
        return 0

    if not MEGAMIND_ROOT.is_dir():
        logger.error("expected %s on megamind", MEGAMIND_ROOT)
        return 2

    _acquire_lock(args.dry_run)
    started = time.time()
    stats = {"moved": 0, "failed": 0, "bytes": 0, "skipped_existing": 0,
             "skipped_unparsed": 0, "planned": 0}
    map_fh = None
    try:
        if args.map_out and not args.dry_run:
            args.map_out.parent.mkdir(parents=True, exist_ok=True)
            map_fh = args.map_out.open("a")
        if not args.skip_archivist:
            migrate_archivist(args.dry_run, map_fh, stats)
        if not args.skip_frigate:
            migrate_frigate(args.dry_run, stats)
    finally:
        if map_fh:
            map_fh.close()
        _release_lock()

    elapsed = time.time() - started
    logger.info("done: %s elapsed=%.1fs", stats, elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
