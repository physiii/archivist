from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from backups_service import get_schedule_config
from documents.chunking import chunk_document_segments
from documents.extract import extract_document_segments
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
from pymilvus.client.types import LoadState
try:
    from pymilvus import Function, FunctionType
except Exception:  # pragma: no cover
    Function = None  # type: ignore
    FunctionType = None  # type: ignore

from transcripts.chunking import TranscriptChunk, build_time_window_chunks
from transcripts.parsers import parse_transcript
from utils import (
    INDEX_TYPE,
    LOCAL_EMBEDDING_DIM,
    LOCAL_EMBEDDING_MODEL,
    METRIC_TYPE,
    NLIST,
    embed_text_to_vector,
    validate_embeddings,
)

try:
    import fcntl
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore


INDEXING_ROOT = Path(os.getenv("VECTORSTORE_INDEXING_DIR", "/indexing"))
RUNS_DIR = INDEXING_ROOT / "runs"
INDEXING_CONFIG_FILE = INDEXING_ROOT / "indexing-config.json"
INDEXING_STATE_FILE = INDEXING_ROOT / "indexing-state.json"
INDEXING_SCHEDULE_STATE_FILE = INDEXING_ROOT / ".indexing-schedule.json"
SCHEDULER_LOCK_FILE = INDEXING_ROOT / ".indexing-scheduler.lock"
RUN_LOCK_FILE = INDEXING_ROOT / ".indexing-run.lock"
RUN_SUMMARY_FILE = "summary.json"

TRANSCRIPT_COLLECTION = "documents_transcripts"
DOCUMENTS_COLLECTION = "documents"
SUPPORTED_EXTS = {".vtt", ".srt", ".tsv", ".txt"}
DOCUMENT_EXTS = {".pdf", ".docx"}
MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".mp4", ".mkv", ".avi", ".mov", ".webm", ".ts"}
ALL_INDEX_EXTS = SUPPORTED_EXTS | DOCUMENT_EXTS | MEDIA_EXTS
INDEXING_CONTENT_VERSION = "transcript_v6"
DOCUMENT_CONTENT_VERSION = "document_v1"
HOST_MOUNT_ROOT = Path(os.getenv("HOST_MOUNT_ROOT", "/host"))
INDEXING_HOST_PATH_FALLBACK = os.getenv("INDEXING_HOST_PATH_FALLBACK", "1").strip().lower() in {"1", "true", "yes"}
LEGACY_PATH_PREFIX_ALIASES = {
    "/mass": "/media/mass",
}
TRANSCRIPT_EXT_PRIORITY = {
    ".vtt": 0,
    ".srt": 1,
    ".tsv": 2,
    ".txt": 3,
}
TRANSCRIPT_PATH_SUFFIX_RE = re.compile(r"(?i)(?:\.ts)?\.(vtt|srt|tsv|txt)$")
# Container path aliases for host paths users commonly enter in the UI.
# Format: "/host/prefix=/container/prefix;/other/host=/other/container"
INDEXING_PATH_ALIASES = os.getenv(
    "INDEXING_PATH_ALIASES",
    "/media/mass=/media/mass;/home/andy/nas_mass=/home/andy/nas_mass",
)
DEFAULT_EXCLUDED_DIR_NAMES = {
    ".cache",
    ".cargo",
    ".colima",
    ".docker",
    ".git",
    ".gradle",
    ".local",
    ".mypy_cache",
    ".next",
    ".npm",
    ".pnpm-store",
    ".pytest_cache",
    ".ruff_cache",
    ".rustup",
    ".tox",
    ".trash",
    ".trash-1000",
    ".venv",
    ".yarn",
    "__pycache__",
    "build",
    "dist",
    "library",
    "node_modules",
    "venv",
}
INDEXING_EXCLUDED_DIR_NAMES = {
    item.strip().lower()
    for item in os.getenv("INDEXING_EXCLUDED_DIR_NAMES", ",".join(sorted(DEFAULT_EXCLUDED_DIR_NAMES))).split(",")
    if item.strip()
}
INDEXING_SKIP_HIDDEN_DIRS = os.getenv("INDEXING_SKIP_HIDDEN_DIRS", "1").strip().lower() in {"1", "true", "yes"}
DEFAULT_MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
DEFAULT_EMBEDDING_HOST = os.getenv("EMBEDDING_HOST", "localhost")
try:
    DEFAULT_EMBEDDING_PORT = int(os.getenv("EMBEDDING_PORT", "8000"))
except (TypeError, ValueError):
    DEFAULT_EMBEDDING_PORT = 8000
try:
    DEFAULT_MILVUS_CONNECT_TIMEOUT = float(os.getenv("MILVUS_CONNECT_TIMEOUT", "3"))
except (TypeError, ValueError):
    DEFAULT_MILVUS_CONNECT_TIMEOUT = 3.0
try:
    DEFAULT_MILVUS_INSERT_TIMEOUT = float(os.getenv("MILVUS_INSERT_TIMEOUT", "60"))
except (TypeError, ValueError):
    DEFAULT_MILVUS_INSERT_TIMEOUT = 60.0
LEVEL_UTTERANCE = 0
LEVEL_DETAIL = 1
LEVEL_TOPIC = 2
LEVEL_DOC = 3
TAGS_FIELD_MAX_LENGTH = 512

DOC_TYPE_BY_EXT = {
    ".vtt": "subtitle_vtt",
    ".srt": "subtitle_srt",
    ".tsv": "transcript_tsv",
    ".txt": "transcript_txt",
    ".pdf": "pdf",
    ".docx": "docx",
}

DOCUMENT_DOC_TYPE_BY_EXT = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "text_document",
}


def required_chunk_field_names() -> set[str]:
    return {
        "id",
        "vector",
        "text",
        "sparse",
        "hash",
        "source_id",
        "path",
        "filehash",
        "t_start_ms",
        "t_end_ms",
        "chunk_duration_s",
        "level",
        "parent_id",
        "doc_type",
        "source_type",
        "topic_label",
        "language",
        "tags",
        "embedding_model",
        "creation_date",
    }


def _chunk_collection_fields() -> list[FieldSchema]:
    return [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=LOCAL_EMBEDDING_DIM),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
        FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="hash", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="filehash", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="t_start_ms", dtype=DataType.INT64),
        FieldSchema(name="t_end_ms", dtype=DataType.INT64),
        FieldSchema(name="chunk_duration_s", dtype=DataType.INT64),
        FieldSchema(name="level", dtype=DataType.INT64),
        FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="topic_label", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=TAGS_FIELD_MAX_LENGTH),
        FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="creation_date", dtype=DataType.INT64),
    ]


def _chunk_collection_functions() -> list[Any]:
    if Function is None or FunctionType is None:
        return []
    return [
        Function(
            name="bm25_fn",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse"],
        )
    ]


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def _serialize_tags(tags: list[str], *, max_length: int = TAGS_FIELD_MAX_LENGTH) -> str:
    """Serialize tags within the Milvus VARCHAR limit while keeping the leading signal."""
    selected: list[str] = []
    for raw_tag in tags:
        clean = re.sub(r"\s+", " ", str(raw_tag or "")).strip()
        if not clean:
            continue
        if len(clean) > 96:
            clean = clean[:95].rstrip() + "…"
        candidate = [*selected, clean]
        encoded = json.dumps(candidate, separators=(",", ":"))
        if len(encoded) > max_length:
            break
        selected.append(clean)
    return json.dumps(selected, separators=(",", ":"))


def _tail(path: Path, lines: int = 120) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readlines()[-lines:])
    except OSError:
        return ""


def _parse_hhmm(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value.strip())
    if not match:
        raise ValueError("time_of_day must be HH:MM (24h).")
    return int(match.group(1)), int(match.group(2))


def _compute_next_run(now: datetime, hhmm: str) -> datetime:
    hour, minute = _parse_hhmm(hhmm)
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        from datetime import timedelta

        candidate = candidate + timedelta(days=1)
    return candidate


def _scheduled_slot_at_or_before(now: datetime, hhmm: str) -> datetime:
    hour, minute = _parse_hhmm(hhmm)
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _append_log(path: Path, line: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip("\n") + "\n")
    except OSError:
        pass


def _write_summary(run_dir: Path, payload: dict[str, Any]) -> None:
    try:
        (run_dir / RUN_SUMMARY_FILE).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _read_summary(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / RUN_SUMMARY_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _run_last_activity_at(run_dir: Path) -> datetime:
    timestamps: list[float] = []
    for path in (run_dir / RUN_SUMMARY_FILE, run_dir / "main.log", run_dir / "debug.log"):
        try:
            timestamps.append(path.stat().st_mtime)
        except OSError:
            continue
    if not timestamps:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(max(timestamps), tz=timezone.utc)


def _reconcile_summary(run_dir: Path, summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if not summary:
        return summary
    if summary.get("status") != "running" or summary.get("finished_at"):
        return summary

    with _lock:
        current_run_id = _state.run_id if _state.running else None
    if current_run_id == run_dir.name:
        return summary

    repaired = dict(summary)
    repaired["status"] = "interrupted"
    repaired["finished_at"] = _iso(_run_last_activity_at(run_dir))
    message = "Indexing worker exited before completing this run."
    errors = repaired.get("errors")
    if not isinstance(errors, list):
        errors = []
    if message not in errors:
        errors.append(message)
    repaired["errors"] = errors
    repaired["last_line"] = repaired.get("last_line") or message
    _write_summary(run_dir, repaired)
    return repaired


def _new_target_id() -> str:
    return f"index_target_{uuid4().hex[:12]}"


def _acquire_lock(path: Path):
    if fcntl is None:
        return None
    fd = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = path.open("w")
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except Exception:
        try:
            if fd is not None:
                fd.close()
        except Exception:
            pass
        return None


def _ensure_root() -> None:
    INDEXING_ROOT.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _seed_config_if_needed() -> None:
    _ensure_root()
    if INDEXING_CONFIG_FILE.exists():
        return
    INDEXING_CONFIG_FILE.write_text(json.dumps({"version": 1, "targets": []}, indent=2), encoding="utf-8")


def _load_config() -> dict[str, Any]:
    _seed_config_if_needed()
    try:
        payload = json.loads(INDEXING_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        payload = {"version": 1, "targets": []}
    targets = payload.get("targets")
    if not isinstance(targets, list):
        targets = []
    clean_targets: list[dict[str, Any]] = []
    for item in targets:
        clean_targets.append(
            {
                "id": str(item.get("id") or _new_target_id()),
                "path": str(item.get("path") or "").strip(),
                "enabled": bool(item.get("enabled", True)),
                "recursive": bool(item.get("recursive", True)),
                "transcript_files": int(item.get("transcript_files") or 0),
                "last_scanned_at": item.get("last_scanned_at"),
                "last_indexed_at": item.get("last_indexed_at"),
                "last_error": item.get("last_error"),
            }
        )
    return {"version": 1, "targets": [t for t in clean_targets if t["path"]]}


def _save_config(config: dict[str, Any]) -> None:
    _ensure_root()
    INDEXING_CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _apply_target_scan_metadata(
    config: dict[str, Any],
    target_id: str,
    count: int,
    scanned_at: str | None,
    last_error: str | None = None,
) -> bool:
    for target in config.get("targets", []):
        if target.get("id") != target_id:
            continue
        target["transcript_files"] = int(count)
        target["last_scanned_at"] = scanned_at
        target["last_error"] = last_error
        return True
    return False


def _persist_target_scan_progress(target_id: str, count: int, last_error: str | None = None) -> None:
    config = _load_config()
    scanned_at = _iso(datetime.now(timezone.utc))
    if _apply_target_scan_metadata(config, target_id=target_id, count=count, scanned_at=scanned_at, last_error=last_error):
        _save_config(config)


def _load_state() -> dict[str, str]:
    if not INDEXING_STATE_FILE.exists():
        return {}
    try:
        payload = json.loads(INDEXING_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    files = payload.get("files")
    if not isinstance(files, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in files.items():
        key_str = str(key)
        value_str = str(value)
        if key_str and value_str:
            out[key_str] = value_str
    return out


def _save_state(files_map: dict[str, str]) -> None:
    _ensure_root()
    payload = {"version": 1, "files": files_map}
    INDEXING_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_schedule_state() -> None:
    if not INDEXING_SCHEDULE_STATE_FILE.exists():
        _schedule.last_triggered_at = None
        return
    try:
        payload = json.loads(INDEXING_SCHEDULE_STATE_FILE.read_text(encoding="utf-8"))
        last_raw = payload.get("last_triggered_at")
        if isinstance(last_raw, str) and last_raw:
            _schedule.last_triggered_at = datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
        else:
            _schedule.last_triggered_at = None
    except Exception:
        _schedule.last_triggered_at = None


def _save_schedule_state() -> None:
    _ensure_root()
    payload = {"last_triggered_at": _iso(_schedule.last_triggered_at)}
    try:
        INDEXING_SCHEDULE_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _backup_linked_schedule_snapshot(now: datetime | None = None) -> dict[str, Any]:
    global _schedule_loaded
    current = now or datetime.now(timezone.utc)
    if not _schedule_loaded:
        _load_schedule_state()
        _schedule_loaded = True
    backup_schedule = get_schedule_config()
    enabled = bool(backup_schedule.get("enabled", True))
    time_of_day = str(backup_schedule.get("time_of_day", "02:00"))
    next_run_at = _compute_next_run(current, time_of_day) if enabled else None
    with _lock:
        last_triggered_at = _schedule.last_triggered_at
    return {
        "source": "backup",
        "enabled": enabled,
        "time_of_day": time_of_day,
        "timezone": str(backup_schedule.get("timezone") or "utc"),
        "next_run_at": _iso(next_run_at),
        "last_triggered_at": _iso(last_triggered_at),
    }


def _resolve_target_root(path: str) -> tuple[Path, bool]:
    raw = Path(str(path or "").strip()).expanduser()
    translated_candidates: list[Path] = []
    candidates: list[Path] = []
    raw_s = str(raw)
    for pair in (INDEXING_PATH_ALIASES or "").split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        host_prefix, container_prefix = pair.split("=", 1)
        host_prefix = host_prefix.strip()
        container_prefix = container_prefix.strip()
        if not host_prefix or not container_prefix:
            continue
        if raw_s == host_prefix or raw_s.startswith(host_prefix + os.sep):
            suffix = raw_s[len(host_prefix):].lstrip("/")
            translated = Path(container_prefix) / suffix if suffix else Path(container_prefix)
            translated_candidates.append(translated)
    # Prefer explicit alias translations first; raw host paths may exist in-container
    # as empty placeholders and can mask the intended mount alias.
    candidates.extend(translated_candidates)
    candidates.append(raw)
    if INDEXING_HOST_PATH_FALLBACK and raw.is_absolute():
        host_root_s = str(HOST_MOUNT_ROOT)
        if raw_s != host_root_s and not raw_s.startswith(host_root_s + os.sep):
            candidates.append(HOST_MOUNT_ROOT / raw_s.lstrip("/"))
    for idx, candidate in enumerate(candidates):
        if candidate.exists():
            return candidate, idx > 0
    return raw, False


def _alias_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for pair in (INDEXING_PATH_ALIASES or "").split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        host_prefix, container_prefix = pair.split("=", 1)
        host_prefix = str(Path(host_prefix.strip()).as_posix()).rstrip("/")
        container_prefix = str(Path(container_prefix.strip()).as_posix()).rstrip("/")
        if host_prefix and container_prefix:
            pairs.append((host_prefix, container_prefix))
    existing_hosts = {host_prefix for host_prefix, _ in pairs}
    for legacy_prefix, canonical_prefix in LEGACY_PATH_PREFIX_ALIASES.items():
        if legacy_prefix not in existing_hosts:
            pairs.append((legacy_prefix, canonical_prefix))
    return pairs


def _to_host_display_path(path: str) -> str:
    clean = str(Path(str(path or "")).as_posix())
    for host_prefix, container_prefix in _alias_pairs():
        if clean == container_prefix or clean.startswith(container_prefix + "/"):
            suffix = clean[len(container_prefix) :]
            return f"{host_prefix}{suffix}"
    return clean


def _to_runtime_path(path: str) -> str:
    clean = str(Path(str(path or "")).as_posix())
    for host_prefix, container_prefix in _alias_pairs():
        if clean == host_prefix or clean.startswith(host_prefix + "/"):
            suffix = clean[len(host_prefix) :]
            return f"{container_prefix}{suffix}"
    return clean


def _legacy_path_variants(path: str) -> set[str]:
    clean = str(Path(str(path or "")).as_posix())
    variants = {clean}
    for legacy_prefix, canonical_prefix in LEGACY_PATH_PREFIX_ALIASES.items():
        if clean == legacy_prefix or clean.startswith(legacy_prefix + "/"):
            variants.add(canonical_prefix + clean[len(legacy_prefix) :])
        if clean == canonical_prefix or clean.startswith(canonical_prefix + "/"):
            variants.add(legacy_prefix + clean[len(canonical_prefix) :])
    return {item for item in variants if item}


def _canonicalize_transcript_path(path: str) -> str:
    clean = str(Path(str(path or "")).as_posix())
    for legacy_prefix, canonical_prefix in LEGACY_PATH_PREFIX_ALIASES.items():
        if clean == legacy_prefix or clean.startswith(legacy_prefix + "/"):
            return canonical_prefix + clean[len(legacy_prefix) :]
    return clean


def _transcript_family_key(path: str) -> str:
    clean = TRANSCRIPT_PATH_SUFFIX_RE.sub("", _canonicalize_transcript_path(path))
    suffix = Path(clean).suffix.lower()
    if suffix in MEDIA_EXTS:
        clean = str(Path(clean).with_suffix(""))
    return clean


def _transcript_job_sort_key(job: dict[str, Any]) -> tuple[int, int, str]:
    suffix = Path(str(job.get("path") or "")).suffix.lower()
    return (TRANSCRIPT_EXT_PRIORITY.get(suffix, 99), len(str(job.get("path") or "")), str(job.get("path") or ""))


def _dedupe_file_jobs(file_jobs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    selected: dict[str, dict[str, Any]] = {}
    skipped_paths: list[str] = []
    for job in sorted(file_jobs, key=lambda item: str(item.get("path") or "")):
        family_key = _transcript_family_key(str(job.get("path") or ""))
        current = selected.get(family_key)
        if current is None:
            selected[family_key] = job
            continue
        if _transcript_job_sort_key(job) < _transcript_job_sort_key(current):
            skipped_paths.append(str(current.get("path") or ""))
            selected[family_key] = job
        else:
            skipped_paths.append(str(job.get("path") or ""))
    deduped_jobs = sorted(selected.values(), key=lambda item: str(item.get("path") or ""))
    return deduped_jobs, skipped_paths


def _canonical_compare_path(path: str | Path) -> str:
    try:
        return str(Path(path).resolve())
    except OSError:
        return str(Path(path).absolute())


def _is_same_or_descendant(path: str | Path, root: str | Path) -> bool:
    path_clean = str(Path(_canonical_compare_path(path)).as_posix()).rstrip("/")
    root_clean = str(Path(_canonical_compare_path(root)).as_posix()).rstrip("/")
    return path_clean == root_clean or path_clean.startswith(root_clean + "/")


def _target_exclude_roots(target: dict[str, Any], targets: list[dict[str, Any]]) -> list[Path]:
    if not bool(target.get("recursive", True)):
        return []
    target_root, _ = _resolve_target_root(str(target.get("path") or ""))
    if not target_root.exists() or not target_root.is_dir():
        return []
    excludes: list[Path] = []
    target_root_cmp = _canonical_compare_path(target_root)
    for other in targets:
        if other.get("id") == target.get("id") or not other.get("enabled", True):
            continue
        other_root, _ = _resolve_target_root(str(other.get("path") or ""))
        if not other_root.exists() or not other_root.is_dir():
            continue
        other_root_cmp = _canonical_compare_path(other_root)
        if other_root_cmp == target_root_cmp:
            continue
        if _is_same_or_descendant(other_root_cmp, target_root_cmp):
            excludes.append(other_root)
    excludes.sort(key=lambda item: str(item))
    return excludes


def _should_exclude_path(path: str | Path, exclude_roots: list[Path] | None) -> bool:
    if not exclude_roots:
        return False
    return any(_is_same_or_descendant(path, root) for root in exclude_roots)


def _walk_dir_allowed(name: str) -> bool:
    clean = str(name or "").strip()
    if not clean:
        return False
    if INDEXING_SKIP_HIDDEN_DIRS and clean.startswith("."):
        return False
    return clean.lower() not in INDEXING_EXCLUDED_DIR_NAMES


def _prune_walk_dirnames(dirpath: str, dirnames: list[str], exclude_roots: list[Path] | None) -> None:
    dirnames[:] = [
        name
        for name in dirnames
        if _walk_dir_allowed(name) and not _should_exclude_path(Path(dirpath) / name, exclude_roots)
    ]


def _target_scan_count(
    path: str,
    recursive: bool,
    exclude_roots: list[Path] | None = None,
    timeout_seconds: float | None = None,
) -> tuple[int, bool]:
    root, _ = _resolve_target_root(path)
    if not root.exists() or not root.is_dir():
        return 0, False
    if timeout_seconds is None:
        timeout_seconds = float(os.getenv("INDEXING_SCAN_TIMEOUT_SECONDS", "3600"))
    deadline = time.monotonic() + max(1.0, float(timeout_seconds))
    count = 0
    timed_out = False
    if recursive:
        for dirpath, dirnames, filenames in os.walk(
            str(root),
            topdown=True,
            onerror=lambda _err: None,
            followlinks=False,
        ):
            if _should_exclude_path(dirpath, exclude_roots):
                dirnames[:] = []
                continue
            _prune_walk_dirnames(dirpath, dirnames, exclude_roots)
            if time.monotonic() >= deadline:
                timed_out = True
                break
            dir_paths: list[str] = []
            for name in filenames:
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                suffix = Path(name).suffix.lower()
                if suffix in ALL_INDEX_EXTS:
                    item = Path(dirpath) / name
                    if not _should_exclude_path(item, exclude_roots):
                        dir_paths.append(str(item.absolute()))
            count += len(_dedupe_directory_paths(dir_paths))
    else:
        try:
            dir_paths = []
            for entry in root.iterdir():
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                try:
                    if entry.is_file() and entry.suffix.lower() in ALL_INDEX_EXTS:
                        dir_paths.append(str(entry.absolute()))
                except OSError:
                    continue
            count = len(_dedupe_directory_paths(dir_paths))
        except OSError:
            return count, timed_out
    return count, timed_out


def _path_is_descendant(path: str, root: str) -> bool:
    path_clean = str(Path(path).as_posix()).rstrip("/")
    root_clean = str(Path(root).as_posix()).rstrip("/")
    return path_clean == root_clean or path_clean.startswith(root_clean + "/")


def _iter_target_files(path: str, recursive: bool) -> list[str]:
    return list(_iter_target_file_paths(path, recursive))


def _dedupe_directory_paths(paths: list[str]) -> list[str]:
    transcript_jobs = []
    document_paths = []
    for read_path in sorted(paths):
        if _treat_as_document(read_path):
            document_paths.append(read_path)
        else:
            display_path = _to_host_display_path(read_path)
            transcript_jobs.append({"path": display_path, "read_path": read_path})
    deduped_transcripts, _ = _dedupe_file_jobs(transcript_jobs)
    out = [str(job.get("read_path") or "") for job in deduped_transcripts if str(job.get("read_path") or "")]
    out.extend(document_paths)
    out.sort()
    return out


def _iter_target_file_paths(path: str, recursive: bool, exclude_roots: list[Path] | None = None):
    root, _ = _resolve_target_root(path)
    if not root.exists() or not root.is_dir():
        return
    timeout_seconds = float(os.getenv("INDEXING_FILE_DISCOVERY_TIMEOUT_SECONDS", "600"))
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    if recursive:
        for dirpath, dirnames, filenames in os.walk(
            str(root),
            topdown=True,
            onerror=lambda _err: None,
            followlinks=False,
        ):
            if _should_exclude_path(dirpath, exclude_roots):
                dirnames[:] = []
                continue
            _prune_walk_dirnames(dirpath, dirnames, exclude_roots)
            if time.monotonic() >= deadline:
                break
            dir_paths: list[str] = []
            for name in filenames:
                if time.monotonic() >= deadline:
                    break
                suffix = Path(name).suffix.lower()
                if suffix not in ALL_INDEX_EXTS:
                    continue
                item = Path(dirpath) / name
                if _should_exclude_path(item, exclude_roots):
                    continue
                dir_paths.append(str(item.absolute()))
            for read_path in _dedupe_directory_paths(dir_paths):
                yield read_path
    else:
        try:
            dir_paths = []
            for item in root.iterdir():
                if time.monotonic() >= deadline:
                    break
                try:
                    if item.is_file() and item.suffix.lower() in ALL_INDEX_EXTS:
                        dir_paths.append(str(item.absolute()))
                except OSError:
                    continue
        except OSError:
            return
        for read_path in _dedupe_directory_paths(dir_paths):
            yield read_path


def _file_hash(path: str) -> str:
    digest = sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _escape_expr(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _milvus_alias(prefix: str = "indexing") -> str:
    return f"{prefix}_{uuid4().hex}"


def _default_milvus_host() -> str:
    return os.getenv("MILVUS_HOST") or DEFAULT_MILVUS_HOST


def _default_embedding_host() -> str:
    return os.getenv("EMBEDDING_HOST") or DEFAULT_EMBEDDING_HOST


def _default_embedding_port() -> int:
    try:
        return int(os.getenv("EMBEDDING_PORT", str(DEFAULT_EMBEDDING_PORT)))
    except (TypeError, ValueError):
        return DEFAULT_EMBEDDING_PORT


def _create_index_best_effort(collection: Collection, field_name: str, index_params: dict[str, Any]) -> None:
    try:
        collection.create_index(field_name=field_name, index_params=index_params, timeout=5)
    except Exception as exc:
        log.warning("Index creation for %s.%s did not finish: %s", collection.name, field_name, exc)


def _ensure_chunk_collection(name: str, description: str, alias: str, ip_address: str | None = None) -> Collection:
    connections.connect(
        alias,
        host=ip_address or _default_milvus_host(),
        port="19530",
        timeout=DEFAULT_MILVUS_CONNECT_TIMEOUT,
    )
    recreate = False
    if utility.has_collection(name, using=alias, timeout=DEFAULT_MILVUS_CONNECT_TIMEOUT):
        existing = Collection(name=name, using=alias)
        fields = {field.name: field for field in existing.schema.fields}
        required = required_chunk_field_names()
        if not required.issubset(fields.keys()):
            recreate = True
        else:
            dim = int(getattr(fields.get("vector"), "params", {}).get("dim", 0) or 0)
            if dim != LOCAL_EMBEDDING_DIM:
                recreate = True
        if recreate:
            existing.drop(timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
    if not utility.has_collection(name, using=alias, timeout=DEFAULT_MILVUS_CONNECT_TIMEOUT):
        schema = CollectionSchema(_chunk_collection_fields(), description=description, functions=_chunk_collection_functions())
        collection = Collection(name=name, schema=schema, using=alias)
        dense_index = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        _create_index_best_effort(collection, "vector", dense_index)
        _create_index_best_effort(
            collection,
            "sparse",
            {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25", "params": {}},
        )
        return collection
    collection = Collection(name=name, using=alias)
    try:
        existing = collection.indexes or []
    except Exception:
        existing = []
    has_vector_index = any(getattr(ix, "field_name", "") == "vector" for ix in existing)
    has_sparse_index = any(getattr(ix, "field_name", "") == "sparse" for ix in existing)
    vector_metric = None
    for ix in existing:
        if getattr(ix, "field_name", "") != "vector":
            continue
        params = getattr(ix, "params", {}) or {}
        metric = params.get("metric_type")
        if metric:
            vector_metric = str(metric).strip().upper()
            break
    if not has_vector_index:
        dense_index = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        _create_index_best_effort(collection, "vector", dense_index)
    elif vector_metric and vector_metric != str(METRIC_TYPE).strip().upper():
        collection.release(timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
        collection.drop_index(index_name="vector", timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
        dense_index = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        _create_index_best_effort(collection, "vector", dense_index)
    if not has_sparse_index:
        _create_index_best_effort(
            collection,
            "sparse",
            {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25", "params": {}},
        )
    return collection


def _ensure_transcripts_collection(alias: str, ip_address: str = "localhost") -> Collection:
    return _ensure_chunk_collection(TRANSCRIPT_COLLECTION, "Transcript chunks", alias=alias, ip_address=ip_address)


def _ensure_documents_collection(alias: str, ip_address: str = "localhost") -> Collection:
    return _ensure_chunk_collection(DOCUMENTS_COLLECTION, "Document chunks", alias=alias, ip_address=ip_address)


def _collection_is_loaded(collection: Collection, *, alias: str) -> bool:
    try:
        return utility.load_state(collection.name, using=alias, timeout=1) == LoadState.Loaded
    except Exception:
        return False


def _delete_source_ids_if_loaded(collection: Collection, source_ids: list[str], *, alias: str) -> bool:
    if not source_ids:
        return False
    seen_source_ids: set[str] = set()
    deleted = False
    for source_id in source_ids:
        if not source_id or source_id in seen_source_ids:
            continue
        seen_source_ids.add(source_id)
        delete_expr = f'source_id == "{_escape_expr(source_id)}"'
        try:
            collection.delete(delete_expr, timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
            deleted = True
        except Exception:
            try:
                if not _collection_is_loaded(collection, alias=alias):
                    collection.load(timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
                collection.delete(delete_expr, timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
                deleted = True
            except Exception:
                pass
    if deleted:
        try:
            collection.flush(timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
        except Exception:
            pass
    return deleted


@dataclass
class RuntimeState:
    run_thread: threading.Thread | None = None
    run_id: str | None = None
    running: bool = False
    stop_requested: bool = False
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    active_step: str | None = None
    progress_current: int = 0
    progress_total: int = 0
    progress_line: str | None = None
    elapsed_seconds: int = 0
    eta_seconds: int | None = None
    files_done: int = 0
    files_total: int = 0
    chunks_done: int = 0
    chunks_total: int = 0
    current_path: str | None = None
    _started_monotonic: float | None = None
    _run_lock_fd: Any | None = None


@dataclass
class ScheduleState:
    last_triggered_at: datetime | None = None


_lock = threading.Lock()
_state = RuntimeState()
_schedule = ScheduleState()
_scheduler_stop = threading.Event()
_scheduler_lock_fd = None
_schedule_loaded = False


def list_indexing_targets() -> list[dict[str, Any]]:
    return _load_config()["targets"]


def add_indexing_target(path: str, enabled: bool = True, recursive: bool = True) -> dict[str, Any]:
    item = {
        "id": _new_target_id(),
        "path": str(path or "").strip(),
        "enabled": bool(enabled),
        "recursive": bool(recursive),
        "transcript_files": 0,
        "last_scanned_at": None,
        "last_indexed_at": None,
        "last_error": None,
    }
    if not item["path"]:
        raise ValueError("path is required")
    config = _load_config()
    config["targets"].append(item)
    _save_config(config)
    return item


def update_indexing_target(target_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    config = _load_config()
    for item in config["targets"]:
        if item["id"] != target_id:
            continue
        if "path" in payload:
            item["path"] = str(payload.get("path") or "").strip()
        if "enabled" in payload:
            item["enabled"] = bool(payload.get("enabled"))
        if "recursive" in payload:
            item["recursive"] = bool(payload.get("recursive"))
        if not item["path"]:
            raise ValueError("path is required")
        _save_config(config)
        return item
    raise FileNotFoundError(target_id)


def delete_indexing_target(target_id: str) -> None:
    config = _load_config()
    before = len(config["targets"])
    config["targets"] = [item for item in config["targets"] if item["id"] != target_id]
    if len(config["targets"]) == before:
        raise FileNotFoundError(target_id)
    _save_config(config)


def _target_excluded_target_paths(target: dict[str, Any], targets: list[dict[str, Any]]) -> list[str]:
    exclude_roots = {_canonical_compare_path(root) for root in _target_exclude_roots(target, targets)}
    if not exclude_roots:
        return []
    paths: list[str] = []
    for other in targets:
        if other.get("id") == target.get("id"):
            continue
        other_root, _ = _resolve_target_root(str(other.get("path") or ""))
        if _canonical_compare_path(other_root) in exclude_roots:
            paths.append(str(other.get("path") or ""))
    return sorted(path for path in paths if path)


def _target_health(target: dict[str, Any], targets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    path = str(target["path"])
    resolved_root, used_host_fallback = _resolve_target_root(path)
    exists = resolved_root.exists()
    readable = os.access(str(resolved_root), os.R_OK) if exists else False
    ready = bool(exists and readable and resolved_root.is_dir())
    excluded_child_targets = _target_excluded_target_paths(target, targets or []) if targets else []
    return {
        "id": target["id"],
        "path": path,
        "enabled": bool(target.get("enabled", True)),
        "recursive": bool(target.get("recursive", True)),
        "exists": exists,
        "readable": readable,
        "ready": ready,
        "transcript_files": int(target.get("transcript_files") or 0),
        "last_scanned_at": target.get("last_scanned_at"),
        "last_indexed_at": target.get("last_indexed_at"),
        "last_error": target.get("last_error"),
        "resolved_path": str(resolved_root),
        "used_host_fallback": used_host_fallback,
        "excluded_child_targets": excluded_child_targets,
    }


def scan_indexing_target(target_id: str) -> dict[str, Any]:
    config = _load_config()
    found = False
    for target in config["targets"]:
        if target["id"] != target_id:
            continue
        found = True
        now = _iso(datetime.now(timezone.utc))
        try:
            exclude_roots = _target_exclude_roots(target, config["targets"])
            interactive_timeout = float(os.getenv("INDEXING_INTERACTIVE_SCAN_TIMEOUT_SECONDS", "30"))
            count, timed_out = _target_scan_count(
                target["path"],
                bool(target.get("recursive", True)),
                exclude_roots=exclude_roots,
                timeout_seconds=interactive_timeout,
            )
            if timed_out and count == 0:
                # If the broad root times out before transcript-heavy leaves are traversed,
                # use configured child-target scan counts as a lower-bound instead of 0.
                for sibling in config["targets"]:
                    sibling_path = str(sibling.get("path") or "")
                    if sibling_path and sibling.get("id") != target["id"] and _path_is_descendant(sibling_path, target["path"]):
                        count = max(count, int(sibling.get("transcript_files") or 0))
            target["transcript_files"] = count
            target["last_scanned_at"] = now
            target["last_error"] = "Scan timed out; transcript count is partial." if timed_out else None
        except Exception as exc:
            target["last_error"] = str(exc)
            target["last_scanned_at"] = now
    if not found:
        raise FileNotFoundError(target_id)
    _save_config(config)
    return get_indexing_overview()


def _latest_runs(limit: int = 10) -> list[dict[str, Any]]:
    if not RUNS_DIR.exists():
        return []
    run_dirs = [item for item in RUNS_DIR.iterdir() if item.is_dir() and item.name.startswith("run_")]
    run_dirs.sort(key=lambda p: p.name, reverse=True)
    out: list[dict[str, Any]] = []
    for run_dir in run_dirs[:limit]:
        summary = _reconcile_summary(run_dir, _read_summary(run_dir)) or {}
        last_line = summary.get("last_line") or _tail(run_dir / "main.log", lines=1).strip() or None
        out.append(
            {
                "run_id": run_dir.name,
                "started_at": run_dir.name.removeprefix("run_"),
                "finished_at": summary.get("finished_at"),
                "status": summary.get("status"),
                "last_line": last_line,
                "files_total": summary.get("files_total"),
                "files_indexed": summary.get("files_indexed"),
                "chunks_total": summary.get("chunks_total"),
                "chunks_indexed": summary.get("chunks_indexed"),
            }
        )
    return out


def _state_status() -> dict[str, Any]:
    with _lock:
        elapsed = _state.elapsed_seconds
        eta = _state.eta_seconds
        if _state.running and _state._started_monotonic is not None:
            elapsed = max(0, int(time.time() - _state._started_monotonic))
            if _state.chunks_done > 0 and _state.chunks_total > _state.chunks_done:
                rate = _state.chunks_done / max(elapsed, 1)
                eta = int(((_state.chunks_total - _state.chunks_done) / rate)) if rate > 0 else None
        return {
            "running": bool(_state.running),
            "pid": os.getpid() if _state.running else None,
            "run_id": _state.run_id,
            "started_at": _iso(_state.started_at),
            "finished_at": _iso(_state.finished_at),
            "exit_code": _state.exit_code,
            "active_step": _state.active_step,
            "progress_current": _state.progress_current,
            "progress_total": _state.progress_total,
            "progress_line": _state.progress_line,
            "elapsed_seconds": elapsed,
            "eta_seconds": eta,
            "files_done": _state.files_done,
            "files_total": _state.files_total,
            "chunks_done": _state.chunks_done,
            "chunks_total": _state.chunks_total,
            "current_path": _state.current_path,
        }


def get_indexing_overview() -> dict[str, Any]:
    _ensure_root()
    config = _load_config()
    target_health = [_target_health(item, config["targets"]) for item in config["targets"]]
    storage_ready = all(t["ready"] for t in target_health if t["enabled"]) if target_health else False
    return {
        "status": _state_status(),
        "timer_schedule": "daily",
        "schedule": _backup_linked_schedule_snapshot(),
        "targets": config["targets"],
        "target_health": target_health,
        "storage_ready": storage_ready,
        "recent_runs": _latest_runs(),
    }


def _release_run_lock() -> None:
    with _lock:
        fd = _state._run_lock_fd
        _state._run_lock_fd = None
    try:
        if fd is not None:
            fd.close()
    except Exception:
        pass


def _build_file_jobs(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for target in targets:
        exclude_roots = _target_exclude_roots(target, targets)
        for read_path in _iter_target_file_paths(
            target["path"],
            bool(target.get("recursive", True)),
            exclude_roots=exclude_roots,
        ):
            jobs.append(
                {
                    "target_id": target["id"],
                    "path": _to_host_display_path(read_path),
                    "read_path": read_path,
                }
            )
    jobs.sort(key=lambda item: item["path"])
    return jobs


def _source_id_for_path(path: str) -> str:
    return str(Path(str(path or "")).as_posix())


def _source_id_candidates(display_path: str, read_path: str) -> list[str]:
    candidates = {
        _source_id_for_path(display_path),
        _source_id_for_path(read_path),
        _source_id_for_path(_to_host_display_path(read_path)),
        _source_id_for_path(_to_runtime_path(display_path)),
    }
    for raw_path in list(candidates):
        for variant in _legacy_path_variants(raw_path):
            candidates.add(_source_id_for_path(variant))
    return [item for item in candidates if item]


def _doc_type_for_path(path: str) -> str:
    return DOC_TYPE_BY_EXT.get(Path(path).suffix.lower(), "transcript")


def _document_doc_type_for_path(path: str) -> str:
    return DOCUMENT_DOC_TYPE_BY_EXT.get(Path(path).suffix.lower(), "document")


def _txt_looks_like_transcript(path: str) -> bool:
    try:
        sample = Path(path).read_text(encoding="utf-8", errors="replace")[:16000]
    except Exception:
        return False
    if not sample.strip():
        return False
    patterns = [
        r"(?m)^\s*\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?\s*-->",
        r"(?m)^\s*\[?\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?\]?",
        r"(?m)^\s*\d+\s*$",
    ]
    if re.search(patterns[0], sample):
        return True
    timestamp_hits = sum(1 for pattern in patterns[1:] if re.search(pattern, sample))
    if timestamp_hits > 0:
        return True
    generic_timestamps = re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?\b", sample)
    return len(generic_timestamps) >= 3


def _treat_as_document(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    if suffix in DOCUMENT_EXTS:
        return True
    if suffix == ".txt":
        return not _txt_looks_like_transcript(path)
    return False


def _collection_name_for_path(path: str) -> str:
    if _treat_as_document(path):
        return DOCUMENTS_COLLECTION
    return TRANSCRIPT_COLLECTION


def _content_version_for_path(path: str) -> str:
    if _treat_as_document(path):
        return DOCUMENT_CONTENT_VERSION
    return INDEXING_CONTENT_VERSION


def _parse_and_chunk(read_path: str, display_path: str) -> tuple[list[TranscriptChunk], str | None]:
    cues, reason = parse_transcript(read_path)
    if not cues:
        return [], reason or "No transcript cues parsed"
    chunks = build_time_window_chunks(
        cues,
        path=display_path,
        source_id=_source_id_for_path(display_path),
        source_type="transcript",
        doc_type=_doc_type_for_path(read_path),
        topic_label=None,
        language=None,
        durations_s=(60, 3600),
        strides_s=(30, 1800),
        min_words_level1=4,
        min_words_level2=8,
    )
    if not chunks:
        return [], "No chunks generated"
    return chunks, None


def _parse_document_and_chunk(read_path: str, display_path: str) -> tuple[list[TranscriptChunk], str | None]:
    segments, reason = extract_document_segments(read_path)
    if not segments:
        return [], reason or "No extractable document text found"
    chunks = chunk_document_segments(
        segments,
        path=display_path,
        source_id=_source_id_for_path(display_path),
        doc_type=_document_doc_type_for_path(read_path),
        source_type="document",
        language=None,
    )
    if not chunks:
        return [], "No document chunks generated"
    return chunks, None


def _is_media_file(path: str) -> bool:
    return Path(path).suffix.lower() in MEDIA_EXTS


def _parse_file_job(read_path: str, display_path: str) -> tuple[list[TranscriptChunk], str | None]:
    if _is_media_file(read_path):
        try:
            from media.pipeline import process_media_file
            process_media_file(read_path)
        except Exception as e:
            return [], f"media pipeline error: {e}"
        return [], "routed:media"
    if _treat_as_document(read_path):
        return _parse_document_and_chunk(read_path, display_path)
    return _parse_and_chunk(read_path, display_path)


def _chunk_hash(chunk: TranscriptChunk) -> str:
    payload = f"{chunk.source_id}|{chunk.t_start_ms}|{chunk.chunk_duration_s}|{chunk.level}|{chunk.tag}|{chunk.text}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _insert_chunks(
    collection: Collection,
    chunks: list[TranscriptChunk],
    filehash: str,
    embedding_host: str,
    embedding_port: int,
    tag_builder=None,
) -> int:
    if not chunks:
        return 0
    creation = int(datetime.now().timestamp())
    rows: list[tuple[list[float], TranscriptChunk, str, str, list[str]]] = []
    embedding_batch_size = 16
    embedding_text_max_chars = 12000
    for start in range(0, len(chunks), embedding_batch_size):
        batch_chunks = chunks[start : start + embedding_batch_size]
        batch_texts = [chunk.text[:embedding_text_max_chars] for chunk in batch_chunks]
        vectors = embed_text_to_vector(
            batch_texts,
            LOCAL_EMBEDDING_MODEL,
            is_local=True,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        validated = validate_embeddings(vectors, LOCAL_EMBEDDING_DIM)
        for vector, chunk in zip(validated, batch_chunks):
            if vector is None:
                continue
            extra_tags = []
            if callable(tag_builder):
                try:
                    built_tags = tag_builder(chunk)
                    if isinstance(built_tags, list):
                        extra_tags = [str(tag).strip() for tag in built_tags if str(tag).strip()]
                except Exception:
                    extra_tags = []
            rows.append((vector, chunk, _chunk_hash(chunk), filehash, extra_tags))
    if not rows:
        return 0
    def _tags_for_chunk(chunk: TranscriptChunk, extra_tags: list[str] | None = None) -> str:
        path_obj = Path(str(chunk.path or ""))
        suffix = path_obj.suffix.lower().lstrip(".")
        tags = [
            chunk.tag,
            f"chunk_tag:{chunk.tag}",
            f"level_{chunk.level}",
            f"duration_{chunk.chunk_duration_s}s",
            f"source_type:{chunk.source_type}",
            f"doc_type:{chunk.doc_type}",
            f"filename:{path_obj.name}",
        ]
        if suffix:
            tags.append(f"file_ext:{suffix}")
        if path_obj.parent.name:
            tags.append(f"parent_dir:{path_obj.parent.name}")
        page_match = re.match(r"page_(\d+)", chunk.tag)
        if page_match:
            tags.append(f"page:{page_match.group(1)}")
            tags.append("segment_kind:page")
        heading_match = re.match(r"heading_(\d+)", chunk.tag)
        if heading_match:
            tags.append(f"heading:{heading_match.group(1)}")
            tags.append("segment_kind:heading")
        block_match = re.match(r"block_(\d+)", chunk.tag)
        if block_match:
            tags.append(f"block:{block_match.group(1)}")
            tags.append("segment_kind:block")
        if chunk.language:
            tags.append(f"language:{chunk.language}")
        if chunk.topic_label:
            tags.append(f"topic:{chunk.topic_label}")
        if extra_tags:
            tags.extend(tag for tag in extra_tags if tag)
        return _serialize_tags(tags)

    fields = [
        "vector",
        "text",
        "hash",
        "source_id",
        "path",
        "filehash",
        "t_start_ms",
        "t_end_ms",
        "chunk_duration_s",
        "level",
        "parent_id",
        "doc_type",
        "source_type",
        "topic_label",
        "language",
        "tags",
        "embedding_model",
        "creation_date",
    ]
    data = [
        [row[0] for row in rows],
        [row[1].text[:65000] for row in rows],
        [row[2] for row in rows],
        [row[1].source_id for row in rows],
        [row[1].path for row in rows],
        [row[3] for row in rows],
        [row[1].t_start_ms for row in rows],
        [row[1].t_end_ms for row in rows],
        [row[1].chunk_duration_s for row in rows],
        [row[1].level for row in rows],
        [row[1].parent_id or "" for row in rows],
        [row[1].doc_type for row in rows],
        [row[1].source_type for row in rows],
        [row[1].topic_label or "" for row in rows],
        [row[1].language or "" for row in rows],
        [_tags_for_chunk(row[1], row[4]) for row in rows],
        [LOCAL_EMBEDDING_MODEL] * len(rows),
        [creation] * len(rows),
    ]
    collection.insert(data, fields=fields, timeout=DEFAULT_MILVUS_INSERT_TIMEOUT)
    return len(rows)


def _run_indexing_job(
    run_id: str,
    run_dir: Path,
    targets: list[dict[str, Any]],
    embedding_host: str,
    embedding_port: int,
    ip_address: str,
) -> None:
    main_log_path = run_dir / "main.log"
    debug_log_path = run_dir / "debug.log"
    summary: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _iso(datetime.now(timezone.utc)),
        "finished_at": None,
        "status": "running",
        "files_total": 0,
        "files_indexed": 0,
        "files_skipped": 0,
        "files_failed": 0,
        "chunks_total": 0,
        "chunks_indexed": 0,
        "errors": [],
        "last_line": None,
    }
    _write_summary(run_dir, summary)

    try:
        alias = _milvus_alias("indexing")
        files_state = _load_state()
        target_indexed_time: dict[str, str] = {}
        target_scan_counts: dict[str, int] = {}
        target_scan_persisted_counts: dict[str, int] = {}
        collections: dict[str, Collection] = {}
        seen_filehash_paths: dict[str, str] = {}
        seen_source_paths: set[str] = set()
        with _lock:
            _state.active_step = "scan"
            _state.files_total = 0
            _state.files_done = 0
            _state.progress_total = 1
            _state.progress_current = 0
            _state.progress_line = "Discovering indexable files"
            _state.current_path = None
        try:
            discovered_files = 0
            _append_log(main_log_path, f"[{run_id}] indexing run started")
            for target in targets:
                target_path = str(target.get("path") or "")
                target_scan_counts[target["id"]] = 0
                target_scan_persisted_counts[target["id"]] = 0
                with _lock:
                    if _state.stop_requested:
                        raise RuntimeError("Indexing stop requested by user.")
                    _state.current_path = target_path
                    _state.progress_line = f"Discovering files under {target_path}"
                exclude_roots = _target_exclude_roots(target, targets)
                for read_path in _iter_target_file_paths(
                    target_path,
                    bool(target.get("recursive", True)),
                    exclude_roots=exclude_roots,
                ):
                    display_path = _to_host_display_path(read_path)
                    source_path = _source_id_for_path(display_path)
                    if source_path in seen_source_paths:
                        _append_log(main_log_path, f"Skipped {display_path}: duplicate path from overlapping target")
                        continue
                    seen_source_paths.add(source_path)
                    discovered_files += 1
                    target_scan_counts[target["id"]] += 1
                    if target_scan_counts[target["id"]] - target_scan_persisted_counts[target["id"]] >= 25:
                        _persist_target_scan_progress(target["id"], target_scan_counts[target["id"]])
                        target_scan_persisted_counts[target["id"]] = target_scan_counts[target["id"]]
                    summary["files_total"] = discovered_files
                    with _lock:
                        if _state.stop_requested:
                            raise RuntimeError("Indexing stop requested by user.")
                        _state.active_step = "scan"
                        _state.current_path = display_path
                        _state.files_total = discovered_files
                        _state.progress_total = max(discovered_files, 1)
                        _state.progress_current = _state.files_done
                        _state.progress_line = f"Scanning {display_path}"
                    chunks, reason = _parse_file_job(read_path, display_path)
                    if reason == "routed:media":
                        summary["files_indexed"] += 1
                        summary.setdefault("files_routed_to_media", 0)
                        summary["files_routed_to_media"] += 1
                        _append_log(main_log_path, f"Routed to media pipeline: {display_path}")
                        with _lock:
                            _state.files_done += 1
                            _state.progress_current = _state.files_done
                        _write_summary(run_dir, summary)
                        continue
                    if not chunks:
                        summary["files_skipped"] += 1
                        if reason:
                            summary["errors"].append(f"{display_path}: {reason}")
                        _append_log(main_log_path, f"Skipped {display_path}: {reason or 'no chunks'}")
                        with _lock:
                            _state.files_done += 1
                            _state.progress_current = _state.files_done
                        _write_summary(run_dir, summary)
                        continue

                    filehash = _file_hash(read_path)
                    duplicate_of = seen_filehash_paths.get(filehash)
                    if duplicate_of:
                        summary["files_skipped"] += 1
                        _append_log(main_log_path, f"Skipped {display_path}: duplicate transcript content of {duplicate_of}")
                        with _lock:
                            _state.files_done += 1
                            _state.progress_current = _state.files_done
                        _write_summary(run_dir, summary)
                        continue

                    seen_filehash_paths[filehash] = display_path
                    summary["chunks_total"] += len(chunks)
                    collection_name = _collection_name_for_path(read_path)
                    content_version = _content_version_for_path(read_path)
                    collection = collections.get(collection_name)
                    if collection is None:
                        if collection_name == DOCUMENTS_COLLECTION:
                            collection = _ensure_documents_collection(alias=alias, ip_address=ip_address)
                        else:
                            collection = _ensure_transcripts_collection(alias=alias, ip_address=ip_address)
                        collections[collection_name] = collection

                    state_token = f"{content_version}|{LOCAL_EMBEDDING_MODEL}|{filehash}"
                    if files_state.get(display_path) == state_token:
                        summary["files_skipped"] += 1
                        with _lock:
                            _state.files_done += 1
                            _state.chunks_done += len(chunks)
                            _state.chunks_total = summary["chunks_total"]
                            _state.progress_total = max(summary["chunks_total"], 1)
                            _state.progress_current = _state.chunks_done
                        _write_summary(run_dir, summary)
                        continue

                    with _lock:
                        _state.active_step = "index"
                        _state.current_path = display_path
                        _state.chunks_total = summary["chunks_total"]
                        _state.progress_total = max(summary["chunks_total"], 1)
                        _state.progress_current = _state.chunks_done
                        _state.progress_line = f"Indexing {display_path}"

                    _delete_source_ids_if_loaded(
                        collection,
                        list(_source_id_candidates(display_path=display_path, read_path=read_path)),
                        alias=alias,
                    )
                    try:
                        inserted = _insert_chunks(
                            collection=collection,
                            chunks=chunks,
                            filehash=filehash,
                            embedding_host=embedding_host,
                            embedding_port=embedding_port,
                        )
                    except Exception as exc:
                        inserted = 0
                        summary["files_failed"] += 1
                        summary["errors"].append(f"{display_path}: embedding/insert failed ({exc})")
                        _append_log(main_log_path, f"Failed {display_path}: embedding/insert failed ({exc})")
                        with _lock:
                            _state.files_done += 1
                            _state.chunks_done += len(chunks)
                            _state.progress_current = _state.chunks_done
                        _write_summary(run_dir, summary)
                        continue

                    if inserted <= 0:
                        summary["files_failed"] += 1
                        summary["errors"].append(f"{display_path}: no valid embeddings generated")
                        _append_log(main_log_path, f"Failed {display_path}: no valid embeddings generated")
                    else:
                        summary["files_indexed"] += 1
                        summary["chunks_indexed"] += inserted
                        files_state[display_path] = state_token
                        target_indexed_time[target["id"]] = _iso(datetime.now(timezone.utc)) or ""
                        _append_log(main_log_path, f"Indexed {display_path}: {inserted} chunks")

                    with _lock:
                        _state.files_done += 1
                        _state.chunks_done += len(chunks)
                        _state.chunks_total = summary["chunks_total"]
                        _state.progress_total = max(summary["chunks_total"], 1)
                        _state.progress_current = _state.chunks_done
                        elapsed = max(1, int(time.time() - (_state._started_monotonic or time.time())))
                        _state.elapsed_seconds = elapsed
                        if _state.chunks_done > 0 and _state.chunks_total > _state.chunks_done:
                            rate = _state.chunks_done / elapsed
                            _state.eta_seconds = int((_state.chunks_total - _state.chunks_done) / rate) if rate > 0 else None
                        else:
                            _state.eta_seconds = 0
                    _write_summary(run_dir, summary)
                _persist_target_scan_progress(target["id"], target_scan_counts[target["id"]])
                target_scan_persisted_counts[target["id"]] = target_scan_counts[target["id"]]
            if summary["files_total"] == 0:
                summary["status"] = "ok"
            _save_state(files_state)
        finally:
            for collection_name, collection in collections.items():
                try:
                    collection.release()
                    log.info("Released indexing collection %s", collection_name)
                except Exception:
                    pass
            try:
                connections.disconnect(alias)
            except Exception:
                pass

        if target_indexed_time or target_scan_counts:
            config = _load_config()
            touched_ids = set(target_indexed_time.keys()) | set(target_scan_counts.keys())
            scanned_at = _iso(datetime.now(timezone.utc))
            for target in config["targets"]:
                if target["id"] in touched_ids:
                    if target["id"] in target_indexed_time:
                        target["last_indexed_at"] = target_indexed_time[target["id"]]
                    if target["id"] in target_scan_counts:
                        target["transcript_files"] = int(target_scan_counts[target["id"]])
                        target["last_scanned_at"] = scanned_at
                        target["last_error"] = None
            _save_config(config)

        if summary["files_failed"] > 0:
            summary["status"] = "failed"
            exit_code = 1
        else:
            summary["status"] = "ok"
            exit_code = 0
        summary["last_line"] = f"Indexed {summary['files_indexed']} files, skipped {summary['files_skipped']}, failed {summary['files_failed']}"
        _append_log(main_log_path, summary["last_line"])
    except RuntimeError as exc:
        summary["status"] = "cancelled"
        summary["errors"].append(str(exc))
        summary["last_line"] = str(exc)
        _append_log(main_log_path, str(exc))
        exit_code = 130
    except Exception as exc:
        summary["status"] = "failed"
        summary["errors"].append(str(exc))
        summary["last_line"] = str(exc)
        _append_log(main_log_path, f"Unhandled indexing error: {exc}")
        exit_code = 1
    finally:
        summary["finished_at"] = _iso(datetime.now(timezone.utc))
        _write_summary(run_dir, summary)
        with _lock:
            _state.running = False
            _state.stop_requested = False
            _state.run_thread = None
            _state.finished_at = datetime.now(timezone.utc)
            _state.exit_code = exit_code
            _state.active_step = None
            _state.progress_line = summary.get("last_line") or f"Indexing finished with status {summary['status']}"
            _state.current_path = None
            _state.eta_seconds = 0
            _state.elapsed_seconds = max(0, int(time.time() - (_state._started_monotonic or time.time())))
        _release_run_lock()


def start_indexing(
    target_ids: list[str] | None = None,
    embedding_host: str | None = None,
    embedding_port: int | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    _ensure_root()
    resolved_embedding_host = embedding_host or _default_embedding_host()
    resolved_embedding_port = int(embedding_port or _default_embedding_port())
    resolved_ip_address = ip_address or _default_milvus_host()
    # Recover from stale lock state after crashes/restarts.
    _release_run_lock()
    config = _load_config()
    if target_ids is None:
        targets = [item for item in config["targets"] if item.get("enabled", True)]
    else:
        ids = {str(item).strip() for item in target_ids if str(item).strip()}
        if not ids:
            raise ValueError("target_ids must contain at least one value")
        targets = [item for item in config["targets"] if item["id"] in ids]
        found = {item["id"] for item in targets}
        missing = ids - found
        if missing:
            raise FileNotFoundError(", ".join(sorted(missing)))
    with _lock:
        if _state.running:
            raise RuntimeError("Indexing is already running.")
    run_lock_fd = _acquire_lock(RUN_LOCK_FILE)
    if run_lock_fd is None:
        raise RuntimeError("Another worker is already running indexing.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{stamp}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    with _lock:
        _state.running = True
        _state.stop_requested = False
        _state.run_id = run_id
        _state.started_at = datetime.now(timezone.utc)
        _state.finished_at = None
        _state.exit_code = None
        _state.active_step = "scan"
        _state.progress_current = 0
        _state.progress_total = 1
        _state.progress_line = "Indexing run started"
        _state.elapsed_seconds = 0
        _state.eta_seconds = None
        _state.files_done = 0
        _state.files_total = 0
        _state.chunks_done = 0
        _state.chunks_total = 0
        _state.current_path = None
        _state._started_monotonic = time.time()
        _state._run_lock_fd = run_lock_fd

    worker = threading.Thread(
        target=_run_indexing_job,
        args=(run_id, run_dir, targets, resolved_embedding_host, resolved_embedding_port, resolved_ip_address),
        daemon=True,
        name="indexing-runner",
    )
    with _lock:
        _state.run_thread = worker
    worker.start()
    return get_indexing_overview()


def start_target_indexing(
    target_id: str,
    embedding_host: str | None = None,
    embedding_port: int | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    clean_id = str(target_id or "").strip()
    if not clean_id:
        raise ValueError("target_id is required")
    return start_indexing(target_ids=[clean_id], embedding_host=embedding_host, embedding_port=embedding_port, ip_address=ip_address)


def stop_indexing() -> dict[str, Any]:
    thread = None
    with _lock:
        if not _state.running:
            raise RuntimeError("No running indexing process found.")
        _state.stop_requested = True
        _state.progress_line = "Stop requested. Finishing current step..."
        thread = _state.run_thread
    if thread is not None:
        thread.join(timeout=10)
    return get_indexing_overview()


def get_indexing_run_logs(run_id: str, tail_lines: int = 180) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(run_id)
    summary = _reconcile_summary(run_dir, _read_summary(run_dir))
    return {
        "main_log_tail": _tail(run_dir / "main.log", lines=tail_lines),
        "debug_log_tail": _tail(run_dir / "debug.log", lines=tail_lines),
        "summary": summary,
    }


def _schedule_worker() -> None:
    while not _scheduler_stop.is_set():
        try:
            now = datetime.now(timezone.utc)
            snapshot = _backup_linked_schedule_snapshot(now)
            if snapshot["enabled"]:
                slot = _scheduled_slot_at_or_before(now, str(snapshot["time_of_day"]))
                with _lock:
                    last_triggered_at = _schedule.last_triggered_at
                due = slot <= now and (last_triggered_at is None or last_triggered_at < slot)
                if due:
                    try:
                        start_indexing(
                            embedding_host=_default_embedding_host(),
                            embedding_port=_default_embedding_port(),
                            ip_address=_default_milvus_host(),
                        )
                        with _lock:
                            _schedule.last_triggered_at = now
                            _save_schedule_state()
                    except Exception:
                        pass
        finally:
            _scheduler_stop.wait(30)


# ── GitHub content indexing ──────────────────────────────────────────

GITHUB_CONTENT_VERSION = "github_v1"
GOOGLE_ARCHIVE_CONTENT_VERSION = "google_archive_v1"
GOOGLE_ARCHIVE_FILE_MAP = {
    "gmail": "gmail_messages.jsonl",
    "calendar": "calendar_events.jsonl",
    "drive": "drive_files.jsonl",
    "chat": "chat_messages.jsonl",
}
GOOGLE_ARCHIVE_DOC_TYPES = {
    "gmail": "gmail_message",
    "calendar": "google_calendar_event",
    "drive": "google_drive_file",
    "chat": "google_chat_message",
}
GOOGLE_ARCHIVE_SOURCE_TYPES = {
    "gmail": "google_gmail",
    "calendar": "google_calendar",
    "drive": "google_drive",
    "chat": "google_chat",
}


def _jsonl_read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    records.append(payload)
    except OSError:
        return []
    return records


def _google_archive_slug(value: str | None) -> str:
    clean = re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().lower()).strip("-")
    return clean or "unknown"


def _google_archive_virtual_path(record: dict) -> str:
    service = _google_archive_slug(record.get("service"))
    account = _google_archive_slug(record.get("account"))
    day = _google_archive_slug(record.get("day")) or "undated"
    record_id = _google_archive_slug(record.get("id"))
    return f"google/{service}/{account}/{day}/{record_id or 'record'}.txt"


def _google_archive_source_id(record: dict) -> str:
    service = _google_archive_slug(record.get("service"))
    account = _google_archive_slug(record.get("account"))
    record_id = _google_archive_slug(record.get("id"))
    if not service or not record_id:
        return ""
    return f"google:{service}:{account}:{record_id}"


def _google_archive_state_key(record: dict) -> str:
    return f"google_archive:{_google_archive_source_id(record)}"


def _google_archive_state_token(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    digest = sha256(payload.encode("utf-8")).hexdigest()
    return f"{GOOGLE_ARCHIVE_CONTENT_VERSION}|{LOCAL_EMBEDDING_MODEL}|{digest}"


def _google_archive_extra_tags(record: dict) -> list[str]:
    service = str(record.get("service") or "").strip().lower()
    account = str(record.get("account") or "").strip()
    account_slug = _google_archive_slug(account)
    day = str(record.get("day") or "").strip()
    tags = [
        "integration:google",
        f"service:{_google_archive_slug(service)}",
        f"account:{account_slug}",
    ]
    if account:
        tags.append(f"account_email:{_google_archive_slug(account)}")
    if day:
        tags.append(f"day:{_google_archive_slug(day)}")
    if service == "gmail":
        for label in list(record.get("labels") or [])[:8]:
            tags.append(f"gmail_label:{_google_archive_slug(label)}")
    elif service == "calendar":
        calendar_id = str(record.get("calendar_id") or "").strip()
        if calendar_id:
            tags.append(f"calendar:{_google_archive_slug(calendar_id)}")
        tags.append(f"all_day:{'true' if record.get('all_day') else 'false'}")
    elif service == "drive":
        mime_type = str(record.get("mime_type") or "").strip()
        if mime_type:
            tags.append(f"mime:{_google_archive_slug(mime_type)}")
        for owner in list(record.get("owners") or [])[:3]:
            tags.append(f"drive_owner:{_google_archive_slug(owner)}")
        if record.get("starred"):
            tags.append("starred:true")
        if record.get("shared"):
            tags.append("shared:true")
    elif service == "chat":
        space = str(record.get("space_display_name") or record.get("space_name") or "").strip()
        sender = str(record.get("sender") or "").strip()
        if space:
            tags.append(f"chat_space:{_google_archive_slug(space)}")
        if sender:
            tags.append(f"chat_sender:{_google_archive_slug(sender)}")
        space_type = str(record.get("space_type") or "").strip()
        if space_type:
            tags.append(f"space_type:{_google_archive_slug(space_type)}")
    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        clean = str(tag).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        deduped.append(clean)
    return deduped[:16]


def _google_archive_record_text(record: dict) -> str:
    service = str(record.get("service") or "").strip().lower()
    parts: list[str] = []
    if service == "gmail":
        parts.extend(
            [
                f"Account: {record.get('account') or ''}",
                f"Subject: {record.get('subject') or ''}",
                f"From: {record.get('from') or ''}",
                f"To: {record.get('to') or ''}",
                f"Cc: {record.get('cc') or ''}",
                f"Date: {record.get('date') or ''}",
                f"Labels: {', '.join(record.get('labels') or [])}",
                f"Snippet: {record.get('snippet') or ''}",
                str(record.get("body") or "").strip(),
            ]
        )
    elif service == "calendar":
        attendees = ", ".join(record.get("attendees") or [])
        parts.extend(
            [
                f"Account: {record.get('account') or ''}",
                f"Calendar: {record.get('calendar_summary') or record.get('calendar_id') or ''}",
                f"Summary: {record.get('summary') or ''}",
                f"Status: {record.get('status') or ''}",
                f"Start: {record.get('start') or ''}",
                f"End: {record.get('end') or ''}",
                f"Location: {record.get('location') or ''}",
                f"Attendees: {attendees}",
                str(record.get("description") or "").strip(),
            ]
        )
    elif service == "drive":
        owners = ", ".join(record.get("owners") or [])
        parents = ", ".join(record.get("parent_ids") or [])
        parts.extend(
            [
                f"Account: {record.get('account') or ''}",
                f"Name: {record.get('name') or ''}",
                f"Mime Type: {record.get('mime_type') or ''}",
                f"Owners: {owners}",
                f"Created: {record.get('created_time') or ''}",
                f"Modified: {record.get('modified_time') or ''}",
                f"Parent IDs: {parents}",
                f"Description: {record.get('description') or ''}",
                f"Shared: {record.get('shared') or False}",
                f"Starred: {record.get('starred') or False}",
                f"Size: {record.get('size') or ''}",
            ]
        )
    elif service == "chat":
        parts.extend(
            [
                f"Account: {record.get('account') or ''}",
                f"Space: {record.get('space_display_name') or record.get('space_name') or ''}",
                f"Space Type: {record.get('space_type') or ''}",
                f"Sender: {record.get('sender') or ''}",
                f"Created: {record.get('create_time') or ''}",
                f"Thread: {record.get('thread_name') or ''}",
                str(record.get("text") or "").strip(),
            ]
        )
    return "\n".join(str(part).strip() for part in parts if str(part).strip()).strip()


def _chunk_google_archive_record(record: dict) -> list[TranscriptChunk]:
    source_id = _google_archive_source_id(record)
    service = str(record.get("service") or "").strip().lower()
    if not source_id or service not in GOOGLE_ARCHIVE_DOC_TYPES:
        return []
    full_text = _google_archive_record_text(record)
    if len(full_text) < 40:
        return []
    path = _google_archive_virtual_path(record)
    doc_type = GOOGLE_ARCHIVE_DOC_TYPES[service]
    source_type = GOOGLE_ARCHIVE_SOURCE_TYPES[service]
    tag_prefix = service
    words = full_text.split()
    max_words = 420
    overlap_words = 70
    if len(words) <= max_words:
        return [
            TranscriptChunk(
                chunk_id=sha256(f"{source_id}|0".encode()).hexdigest()[:24],
                source_id=source_id,
                path=path,
                text=full_text,
                t_start_ms=0,
                t_end_ms=0,
                chunk_duration_s=0,
                level=0,
                parent_id=None,
                doc_type=doc_type,
                source_type=source_type,
                topic_label=_google_archive_slug(record.get("account")),
                language=None,
                tag=f"{tag_prefix}_record",
            )
        ]
    step = max(max_words - overlap_words, 1)
    chunks: list[TranscriptChunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        piece = " ".join(words[start:end]).strip()
        if piece:
            chunks.append(
                TranscriptChunk(
                    chunk_id=sha256(f"{source_id}|{index}".encode()).hexdigest()[:24],
                    source_id=source_id,
                    path=path,
                    text=piece,
                    t_start_ms=0,
                    t_end_ms=0,
                    chunk_duration_s=0,
                    level=0,
                    parent_id=None,
                    doc_type=doc_type,
                    source_type=source_type,
                    topic_label=_google_archive_slug(record.get("account")),
                    language=None,
                    tag=f"{tag_prefix}_record_p{index}",
                )
            )
        index += 1
        if end >= len(words):
            break
        start += step
    return chunks


def index_google_archive_content(
    archive_root: str | Path,
    *,
    services: set[str] | None = None,
    embedding_host: str | None = None,
    embedding_port: int | None = None,
    ip_address: str | None = None,
) -> dict:
    import logging

    log = logging.getLogger(__name__)
    root = Path(archive_root)
    resolved_embedding_host = embedding_host or _default_embedding_host()
    resolved_embedding_port = int(embedding_port or _default_embedding_port())
    resolved_ip_address = ip_address or _default_milvus_host()
    selected_services = {str(item).strip().lower() for item in (services or GOOGLE_ARCHIVE_FILE_MAP.keys()) if str(item).strip()}
    summary: dict[str, Any] = {
        "records_seen": 0,
        "records_indexed": 0,
        "chunks_inserted": 0,
        "errors": [],
        "by_service": {},
    }
    if not root.exists():
        summary["errors"].append(f"archive root missing: {root}")
        return summary

    alias = _milvus_alias("google_archive_indexing")
    collection = None
    pending_entries: list[tuple[TranscriptChunk, str, list[str], str, str, str, int, str]] = []
    files_state: dict[str, str] = {}

    def _flush_pending() -> None:
        nonlocal pending_entries, files_state
        if not pending_entries:
            return
        source_ids = []
        state_updates: list[tuple[str, str, str, int, str]] = []
        service_chunk_totals: dict[str, int] = {}
        for _, _, _, source_id, state_key, state_token, chunk_count, service in pending_entries:
            source_ids.append(source_id)
            state_updates.append((state_key, state_token, source_id, chunk_count, service))
        _delete_source_ids_if_loaded(collection, source_ids, alias=alias)
        try:
            inserted = _insert_chunks(
                collection=collection,
                chunks=[entry[0] for entry in pending_entries],
                filehash="google_archive_batch",
                embedding_host=resolved_embedding_host,
                embedding_port=resolved_embedding_port,
                tag_builder=lambda chunk: next((entry[2] for entry in pending_entries if entry[0].chunk_id == chunk.chunk_id), []),
            )
            if inserted > 0:
                for state_key, state_token, source_id, chunk_count, service in state_updates:
                    files_state[state_key] = state_token
                _save_state(files_state)
                inserted_source_ids: set[str] = set()
                for _, _, _, source_id, state_key, _, chunk_count, service in pending_entries:
                    if source_id in inserted_source_ids:
                        continue
                    inserted_source_ids.add(source_id)
                    summary["records_indexed"] += 1
                    service_summary = summary["by_service"].setdefault(
                        service,
                        {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0},
                    )
                    service_summary["records_indexed"] += 1
                    service_chunk_totals[service] = service_chunk_totals.get(service, 0) + chunk_count
                for service, chunk_total in service_chunk_totals.items():
                    summary["by_service"][service]["chunks_inserted"] += chunk_total
                summary["chunks_inserted"] += inserted
        except Exception as exc:
            log.warning("Google archive batch indexing failed; retrying per record: %s", exc)
            summary["errors"].append(f"google archive batch: {exc}")
            by_source: dict[str, list[tuple[TranscriptChunk, str, list[str], str, str, str, int, str]]] = {}
            for entry in pending_entries:
                by_source.setdefault(entry[3], []).append(entry)
            for source_id, source_entries in by_source.items():
                state_key = source_entries[0][4]
                state_token = source_entries[0][5]
                chunk_count = source_entries[0][6]
                service = source_entries[0][7]
                try:
                    inserted = _insert_chunks(
                        collection=collection,
                        chunks=[entry[0] for entry in source_entries],
                        filehash="google_archive_record",
                        embedding_host=resolved_embedding_host,
                        embedding_port=resolved_embedding_port,
                        tag_builder=lambda chunk, record_entries=source_entries: next((entry[2] for entry in record_entries if entry[0].chunk_id == chunk.chunk_id), []),
                    )
                    if inserted > 0:
                        files_state[state_key] = state_token
                        _save_state(files_state)
                        summary["records_indexed"] += 1
                        service_summary = summary["by_service"].setdefault(
                            service,
                            {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0},
                        )
                        service_summary["records_indexed"] += 1
                        service_summary["chunks_inserted"] += inserted
                        summary["chunks_inserted"] += inserted
                except Exception as record_exc:
                    summary["errors"].append(f"{source_id}: {record_exc}")
                    log.warning("Failed to index Google archive record %s: %s", source_id, record_exc)
        pending_entries = []

    try:
        collection = _ensure_documents_collection(alias=alias, ip_address=resolved_ip_address)
        files_state = _load_state()
        for account_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            for service, filename in GOOGLE_ARCHIVE_FILE_MAP.items():
                if service not in selected_services:
                    continue
                service_summary = summary["by_service"].setdefault(
                    service,
                    {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0},
                )
                for record in _jsonl_read_records(account_dir / filename):
                    record = dict(record)
                    record.setdefault("service", service)
                    source_id = _google_archive_source_id(record)
                    state_key = _google_archive_state_key(record)
                    state_token = _google_archive_state_token(record)
                    summary["records_seen"] += 1
                    service_summary["records_seen"] += 1
                    if not source_id:
                        continue
                    if files_state.get(state_key) == state_token:
                        continue
                    chunks = _chunk_google_archive_record(record)
                    if not chunks:
                        files_state[state_key] = state_token
                        continue
                    filehash = sha256(f"{source_id}|{state_token}".encode("utf-8")).hexdigest()
                    extra_tags = _google_archive_extra_tags(record)
                    pending_entries.extend(
                        (chunk, filehash, extra_tags, source_id, state_key, state_token, len(chunks), service)
                        for chunk in chunks
                    )
                    if len(pending_entries) >= 96:
                        _flush_pending()
        _flush_pending()
        _save_state(files_state)
        log.info(
            "Google archive indexing complete: %d seen, %d indexed, %d chunks",
            summary["records_seen"],
            summary["records_indexed"],
            summary["chunks_inserted"],
        )
    except Exception as exc:
        summary["errors"].append(f"Milvus connection/indexing failed: {exc}")
        log.exception("Google archive indexing failed")
    finally:
        if collection is not None:
            try:
                collection.release()
                log.info("Released Google archive indexing collection %s", DOCUMENTS_COLLECTION)
            except Exception:
                pass
        try:
            connections.disconnect(alias)
        except Exception:
            pass

    return summary


def _chunk_github_item(item: dict) -> list[TranscriptChunk]:
    """Convert a single GitHub content record into TranscriptChunk objects."""
    source_id = item.get("source_id", "")
    doc_type = item.get("doc_type", "github_issue")
    title = str(item.get("title") or "").strip()
    body = str(item.get("body") or "").strip()
    comments = item.get("comments") or []

    # Assemble full text: title + body + comments
    parts = []
    if title:
        parts.append(title)
    if body:
        parts.append(body)
    for comment in comments:
        c = str(comment).strip()
        if c:
            parts.append(c)

    full_text = "\n\n".join(parts).strip()
    if not full_text or len(full_text) < 40:
        return []

    # Build tags for metadata
    repo = item.get("repo", "")
    labels = item.get("labels") or []
    state = item.get("state", "")
    tag_parts = [f"repo:{repo}", f"state:{state}"]
    for label in labels[:5]:
        tag_parts.append(f"label:{label}")

    # For short items (< ~500 words), keep as single chunk.
    # For longer items, split into overlapping word windows.
    words = full_text.split()
    target_words = 320
    max_words = 520
    overlap_words = 80
    chunks: list[TranscriptChunk] = []

    if len(words) <= max_words:
        # Single chunk
        chunk_tag = f"github_{doc_type.replace('github_', '')}_{source_id.replace('/', '_').replace('#', '_')}"
        chunks.append(
            TranscriptChunk(
                chunk_id=sha256(f"{source_id}|0|{chunk_tag}".encode()).hexdigest()[:24],
                source_id=source_id,
                path=f"github/{source_id}",
                text=full_text,
                t_start_ms=0,
                t_end_ms=0,
                chunk_duration_s=0,
                level=0,
                parent_id=None,
                doc_type=doc_type,
                source_type="github",
                topic_label=None,
                language=None,
                tag=chunk_tag,
            )
        )
    else:
        # Split into word-window chunks
        step = max(target_words - overlap_words, 1)
        idx = 0
        start = 0
        while start < len(words):
            end = min(start + max_words, len(words))
            chunk_text = " ".join(words[start:end])
            chunk_tag = f"github_{doc_type.replace('github_', '')}_{source_id.replace('/', '_').replace('#', '_')}_p{idx}"
            chunks.append(
                TranscriptChunk(
                    chunk_id=sha256(f"{source_id}|{idx}|{chunk_tag}".encode()).hexdigest()[:24],
                    source_id=source_id,
                    path=f"github/{source_id}",
                    text=chunk_text,
                    t_start_ms=0,
                    t_end_ms=0,
                    chunk_duration_s=0,
                    level=0,
                    parent_id=None,
                    doc_type=doc_type,
                    source_type="github",
                    topic_label=None,
                    language=None,
                    tag=chunk_tag,
                )
            )
            idx += 1
            if start + max_words >= len(words):
                break
            start += step

    return chunks


def index_github_content(
    embedding_host: str | None = None,
    embedding_port: int | None = None,
    ip_address: str | None = None,
) -> dict:
    """Fetch GitHub content and index it into the documents vector store.

    Returns a summary dict with counts of items processed and chunks inserted.
    """
    import logging

    log = logging.getLogger(__name__)
    resolved_embedding_host = embedding_host or _default_embedding_host()
    resolved_embedding_port = int(embedding_port or _default_embedding_port())
    resolved_ip_address = ip_address or _default_milvus_host()
    summary: dict = {"items_fetched": 0, "items_indexed": 0, "chunks_inserted": 0, "errors": []}

    try:
        from github_service import fetch_github_content_for_indexing, GITHUB_TOKEN
        if not GITHUB_TOKEN:
            summary["errors"].append("GITHUB_TOKEN not set")
            return summary
    except ImportError as exc:
        summary["errors"].append(f"github_service not available: {exc}")
        return summary

    try:
        content = fetch_github_content_for_indexing()
    except Exception as exc:
        summary["errors"].append(f"Failed to fetch GitHub content: {exc}")
        return summary

    summary["items_fetched"] = len(content)
    if not content:
        return summary

    # Connect to Milvus and ensure the documents collection exists.
    alias = _milvus_alias("github_indexing")
    collection = None
    try:
        collection = _ensure_documents_collection(alias=alias, ip_address=resolved_ip_address)

        # Load state to check for already-indexed items.
        files_state = _load_state()

        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 5

        for item in content:
            source_id = item.get("source_id", "")
            updated_at = item.get("updated_at", "")
            state_token = f"{GITHUB_CONTENT_VERSION}|{LOCAL_EMBEDDING_MODEL}|{source_id}|{updated_at}"
            state_key = f"github:{source_id}"

            # Skip if already indexed with same version and update time.
            if files_state.get(state_key) == state_token:
                continue

            chunks = _chunk_github_item(item)
            if not chunks:
                continue

            # Delete existing chunks for this source_id before re-inserting.
            _delete_source_ids_if_loaded(collection, [source_id], alias=alias)

            filehash = sha256(f"{source_id}|{updated_at}".encode()).hexdigest()
            try:
                inserted = _insert_chunks(
                    collection=collection,
                    chunks=chunks,
                    filehash=filehash,
                    embedding_host=resolved_embedding_host,
                    embedding_port=resolved_embedding_port,
                )
                if inserted > 0:
                    summary["items_indexed"] += 1
                    summary["chunks_inserted"] += inserted
                    files_state[state_key] = state_token
                    consecutive_failures = 0
            except Exception as exc:
                summary["errors"].append(f"{source_id}: {exc}")
                log.warning("Failed to index GitHub item %s: %s", source_id, exc)
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.warning(
                        "Aborting GitHub indexing after %d consecutive failures (last: %s)",
                        consecutive_failures, exc,
                    )
                    break

        _save_state(files_state)
        log.info(
            "GitHub indexing complete: %d items, %d indexed, %d chunks",
            summary["items_fetched"], summary["items_indexed"], summary["chunks_inserted"],
        )
    except Exception as exc:
        summary["errors"].append(f"Milvus connection/indexing failed: {exc}")
        log.exception("GitHub content indexing failed")
    finally:
        if collection is not None:
            try:
                collection.release()
                log.info("Released GitHub indexing collection %s", DOCUMENTS_COLLECTION)
            except Exception:
                pass
        try:
            connections.disconnect(alias)
        except Exception:
            pass

    return summary


def start_scheduler_best_effort() -> None:
    global _scheduler_lock_fd
    global _schedule_loaded
    if _scheduler_lock_fd is not None:
        return
    _scheduler_lock_fd = _acquire_lock(SCHEDULER_LOCK_FILE)
    if _scheduler_lock_fd is None:
        return
    _load_schedule_state()
    _schedule_loaded = True
    thread = threading.Thread(target=_schedule_worker, daemon=True, name="indexing-scheduler")
    thread.start()
