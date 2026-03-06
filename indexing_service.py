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

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
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
RUN_LOCK_FILE = INDEXING_ROOT / ".indexing-run.lock"
RUN_SUMMARY_FILE = "summary.json"

TRANSCRIPT_COLLECTION = "documents_transcripts"
SUPPORTED_EXTS = {".vtt", ".srt", ".tsv", ".txt"}
INDEXING_CONTENT_VERSION = "transcript_v6"
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
LEVEL_UTTERANCE = 0
LEVEL_DETAIL = 1
LEVEL_TOPIC = 2
LEVEL_DOC = 3

DOC_TYPE_BY_EXT = {
    ".vtt": "subtitle_vtt",
    ".srt": "subtitle_srt",
    ".tsv": "transcript_tsv",
    ".txt": "transcript_txt",
}


def required_transcript_field_names() -> set[str]:
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


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def _tail(path: Path, lines: int = 120) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readlines()[-lines:])
    except OSError:
        return ""


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
    return TRANSCRIPT_PATH_SUFFIX_RE.sub("", _canonicalize_transcript_path(path))


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


def _target_scan_count(path: str, recursive: bool) -> tuple[int, bool]:
    root, _ = _resolve_target_root(path)
    if not root.exists() or not root.is_dir():
        return 0, False
    timeout_seconds = float(os.getenv("INDEXING_SCAN_TIMEOUT_SECONDS", "3600"))
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    count = 0
    timed_out = False
    if recursive:
        for dirpath, _, filenames in os.walk(
            str(root),
            topdown=True,
            onerror=lambda _err: None,
            followlinks=True,
        ):
            if time.monotonic() >= deadline:
                timed_out = True
                break
            for name in filenames:
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                suffix = Path(name).suffix.lower()
                if suffix in SUPPORTED_EXTS:
                    count += 1
    else:
        try:
            for entry in root.iterdir():
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                try:
                    if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTS:
                        count += 1
                except OSError:
                    continue
        except OSError:
            return count, timed_out
    return count, timed_out


def _path_is_descendant(path: str, root: str) -> bool:
    path_clean = str(Path(path).as_posix()).rstrip("/")
    root_clean = str(Path(root).as_posix()).rstrip("/")
    return path_clean == root_clean or path_clean.startswith(root_clean + "/")


def _iter_target_files(path: str, recursive: bool) -> list[str]:
    root, _ = _resolve_target_root(path)
    if not root.exists() or not root.is_dir():
        return []
    out: list[str] = []
    timeout_seconds = float(os.getenv("INDEXING_FILE_DISCOVERY_TIMEOUT_SECONDS", "600"))
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    if recursive:
        for dirpath, _, filenames in os.walk(
            str(root),
            topdown=True,
            onerror=lambda _err: None,
            followlinks=True,
        ):
            if time.monotonic() >= deadline:
                break
            for name in filenames:
                if time.monotonic() >= deadline:
                    break
                suffix = Path(name).suffix.lower()
                if suffix not in SUPPORTED_EXTS:
                    continue
                item = Path(dirpath) / name
                try:
                    out.append(str(item.resolve()))
                except OSError:
                    continue
    else:
        try:
            for item in root.iterdir():
                if time.monotonic() >= deadline:
                    break
                try:
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS:
                        out.append(str(item.resolve()))
                except OSError:
                    continue
        except OSError:
            return out
    out.sort()
    return out


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


def _ensure_transcripts_collection(alias: str, ip_address: str = "localhost") -> Collection:
    connections.connect(alias, host=ip_address, port="19530")
    recreate = False
    if utility.has_collection(TRANSCRIPT_COLLECTION, using=alias):
        existing = Collection(name=TRANSCRIPT_COLLECTION, using=alias)
        fields = {field.name: field for field in existing.schema.fields}
        required = required_transcript_field_names()
        if not required.issubset(fields.keys()):
            recreate = True
        else:
            dim = int(getattr(fields.get("vector"), "params", {}).get("dim", 0) or 0)
            if dim != LOCAL_EMBEDDING_DIM:
                recreate = True
        if recreate:
            existing.drop()
    if not utility.has_collection(TRANSCRIPT_COLLECTION, using=alias):
        fields = [
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
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="creation_date", dtype=DataType.INT64),
        ]
        functions = []
        if Function is not None and FunctionType is not None:
            bm25_fn = Function(
                name="bm25_fn",
                function_type=FunctionType.BM25,
                input_field_names=["text"],
                output_field_names=["sparse"],
            )
            functions = [bm25_fn]
        schema = CollectionSchema(fields, description="Transcript chunks", functions=functions)
        collection = Collection(name=TRANSCRIPT_COLLECTION, schema=schema, using=alias)
        dense_index = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        collection.create_index(field_name="vector", index_params=dense_index)
        collection.create_index(
            field_name="sparse",
            index_params={"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25", "params": {}},
        )
        return collection
    collection = Collection(name=TRANSCRIPT_COLLECTION, using=alias)
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
        collection.create_index(field_name="vector", index_params=dense_index)
    elif vector_metric and vector_metric != str(METRIC_TYPE).strip().upper():
        collection.release()
        collection.drop_index(index_name="vector")
        dense_index = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        collection.create_index(field_name="vector", index_params=dense_index)
    if not has_sparse_index:
        collection.create_index(
            field_name="sparse",
            index_params={"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25", "params": {}},
        )
    return collection


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


_lock = threading.Lock()
_state = RuntimeState()


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


def _target_health(target: dict[str, Any]) -> dict[str, Any]:
    path = str(target["path"])
    resolved_root, used_host_fallback = _resolve_target_root(path)
    exists = resolved_root.exists()
    readable = os.access(str(resolved_root), os.R_OK) if exists else False
    ready = bool(exists and readable and resolved_root.is_dir())
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
            count, timed_out = _target_scan_count(target["path"], bool(target.get("recursive", True)))
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
        summary = _read_summary(run_dir) or {}
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
    target_health = [_target_health(item) for item in config["targets"]]
    storage_ready = all(t["ready"] for t in target_health if t["enabled"]) if target_health else False
    return {
        "status": _state_status(),
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
        files = _iter_target_files(target["path"], bool(target.get("recursive", True)))
        for read_path in files:
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


def _chunk_hash(chunk: TranscriptChunk) -> str:
    payload = f"{chunk.source_id}|{chunk.t_start_ms}|{chunk.chunk_duration_s}|{chunk.level}|{chunk.tag}|{chunk.text}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _insert_chunks(
    collection: Collection,
    chunks: list[TranscriptChunk],
    filehash: str,
    embedding_host: str,
    embedding_port: int,
) -> int:
    if not chunks:
        return 0
    creation = int(datetime.now().timestamp())
    rows: list[tuple[list[float], TranscriptChunk, str]] = []
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
            rows.append((vector, chunk, _chunk_hash(chunk)))
    if not rows:
        return 0
    def _tags_for_chunk(chunk: TranscriptChunk) -> str:
        tags = [
            chunk.tag,
            f"level_{chunk.level}",
            f"duration_{chunk.chunk_duration_s}s",
            f"source_type:{chunk.source_type}",
            f"doc_type:{chunk.doc_type}",
        ]
        if chunk.language:
            tags.append(f"language:{chunk.language}")
        if chunk.topic_label:
            tags.append(f"topic:{chunk.topic_label}")
        return json.dumps(tags)

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
        [filehash] * len(rows),
        [row[1].t_start_ms for row in rows],
        [row[1].t_end_ms for row in rows],
        [row[1].chunk_duration_s for row in rows],
        [row[1].level for row in rows],
        [row[1].parent_id or "" for row in rows],
        [row[1].doc_type for row in rows],
        [row[1].source_type for row in rows],
        [row[1].topic_label or "" for row in rows],
        [row[1].language or "" for row in rows],
        [_tags_for_chunk(row[1]) for row in rows],
        [LOCAL_EMBEDDING_MODEL] * len(rows),
        [creation] * len(rows),
    ]
    collection.insert(data, fields=fields)
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
        file_jobs: list[dict[str, Any]] = []
        with _lock:
            _state.active_step = "scan"
            _state.files_total = 0
            _state.files_done = 0
            _state.progress_total = 1
            _state.progress_current = 0
            _state.progress_line = "Discovering transcript files"
            _state.current_path = None
        for target in targets:
            target_path = str(target.get("path") or "")
            with _lock:
                if _state.stop_requested:
                    raise RuntimeError("Indexing stop requested by user.")
                _state.current_path = target_path
                _state.progress_line = f"Discovering files under {target_path}"
            files = _iter_target_files(target_path, bool(target.get("recursive", True)))
            for read_path in files:
                file_jobs.append(
                    {
                        "target_id": target["id"],
                        "path": _to_host_display_path(read_path),
                        "read_path": read_path,
                    }
                )
            with _lock:
                _state.files_total = len(file_jobs)
                _state.progress_total = max(len(file_jobs), 1)
                _state.progress_current = 0

        file_jobs, duplicate_family_paths = _dedupe_file_jobs(file_jobs)
        file_jobs.sort(key=lambda item: item["path"])
        summary["files_total"] = len(file_jobs)
        _append_log(main_log_path, f"[{run_id}] indexing run started with {len(file_jobs)} candidate files")
        if duplicate_family_paths:
            _append_log(main_log_path, f"Skipped {len(duplicate_family_paths)} lower-priority sibling transcript files")

        parsed_jobs: list[dict[str, Any]] = []
        seen_filehash_paths: dict[str, str] = {}
        with _lock:
            _state.active_step = "scan"
            _state.files_total = len(file_jobs)
            _state.files_done = 0
            _state.progress_total = max(len(file_jobs), 1)
            _state.progress_current = 0
            _state.progress_line = "Scanning transcript files"
            _state.current_path = None

        for idx, job in enumerate(file_jobs, start=1):
            with _lock:
                if _state.stop_requested:
                    raise RuntimeError("Indexing stop requested by user.")
                _state.files_done = idx - 1
                _state.progress_current = idx - 1
                _state.current_path = job["path"]
                _state.progress_line = f"Scanning {job['path']}"
            chunks, reason = _parse_and_chunk(str(job["read_path"]), str(job["path"]))
            if chunks:
                job["chunks"] = chunks
                job["filehash"] = _file_hash(str(job["read_path"]))
                duplicate_of = seen_filehash_paths.get(str(job["filehash"]))
                if duplicate_of:
                    summary["files_skipped"] += 1
                    _append_log(main_log_path, f"Skipped {job['path']}: duplicate transcript content of {duplicate_of}")
                else:
                    seen_filehash_paths[str(job["filehash"])] = str(job["path"])
                    parsed_jobs.append(job)
                    summary["chunks_total"] += len(chunks)
            else:
                summary["files_skipped"] += 1
                if reason:
                    summary["errors"].append(f"{job['path']}: {reason}")
                _append_log(main_log_path, f"Skipped {job['path']}: {reason or 'no chunks'}")
            with _lock:
                _state.files_done = idx
                _state.progress_current = idx
            _write_summary(run_dir, summary)

        with _lock:
            _state.active_step = "index"
            _state.progress_total = max(summary["chunks_total"], 1)
            _state.progress_current = 0
            _state.chunks_total = summary["chunks_total"]
            _state.chunks_done = 0
            _state.progress_line = "Embedding and inserting chunks"
            _state.current_path = None

        alias = _milvus_alias("transcripts")
        files_state = _load_state()
        target_indexed_time: dict[str, str] = {}
        try:
            collection = _ensure_transcripts_collection(alias=alias, ip_address=ip_address)
            try:
                collection.load()
            except Exception:
                pass
            if summary["chunks_total"] == 0:
                summary["status"] = "ok"
            for job in parsed_jobs:
                with _lock:
                    if _state.stop_requested:
                        raise RuntimeError("Indexing stop requested by user.")
                    _state.current_path = job["path"]
                    _state.progress_line = f"Indexing {job['path']}"
                filehash = str(job["filehash"])
                path = str(job["path"])
                read_path = str(job.get("read_path") or path)
                chunks: list[TranscriptChunk] = job["chunks"]
                state_token = f"{INDEXING_CONTENT_VERSION}|{LOCAL_EMBEDDING_MODEL}|{filehash}"
                if files_state.get(path) == state_token:
                    summary["files_skipped"] += 1
                    with _lock:
                        _state.chunks_done += len(chunks)
                        _state.progress_current = _state.chunks_done
                    continue
                for source_id in _source_id_candidates(display_path=path, read_path=read_path):
                    delete_expr = f'source_id == "{_escape_expr(source_id)}"'
                    try:
                        collection.delete(delete_expr)
                    except Exception:
                        pass
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
                    summary["errors"].append(f"{path}: embedding/insert failed ({exc})")
                    _append_log(main_log_path, f"Failed {path}: embedding/insert failed ({exc})")
                    with _lock:
                        _state.chunks_done += len(chunks)
                        _state.progress_current = _state.chunks_done
                    _write_summary(run_dir, summary)
                    continue
                if inserted <= 0:
                    summary["files_failed"] += 1
                    summary["errors"].append(f"{path}: no valid embeddings generated")
                    _append_log(main_log_path, f"Failed {path}: no valid embeddings generated")
                else:
                    summary["files_indexed"] += 1
                    summary["chunks_indexed"] += inserted
                    files_state[path] = state_token
                    target_indexed_time[job["target_id"]] = _iso(datetime.now(timezone.utc)) or ""
                    _append_log(main_log_path, f"Indexed {path}: {inserted} chunks")
                with _lock:
                    _state.chunks_done += len(chunks)
                    _state.progress_current = _state.chunks_done
                    elapsed = max(1, int(time.time() - (_state._started_monotonic or time.time())))
                    _state.elapsed_seconds = elapsed
                    if _state.chunks_done > 0 and _state.chunks_total > _state.chunks_done:
                        rate = _state.chunks_done / elapsed
                        _state.eta_seconds = int((_state.chunks_total - _state.chunks_done) / rate) if rate > 0 else None
                    else:
                        _state.eta_seconds = 0
                _write_summary(run_dir, summary)
            _save_state(files_state)
        finally:
            try:
                connections.disconnect(alias)
            except Exception:
                pass

        if target_indexed_time:
            config = _load_config()
            touched_ids = set(target_indexed_time.keys())
            for target in config["targets"]:
                if target["id"] in touched_ids:
                    target["last_indexed_at"] = target_indexed_time[target["id"]]
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
    embedding_host: str = "localhost",
    embedding_port: int = 8000,
    ip_address: str = "localhost",
) -> dict[str, Any]:
    _ensure_root()
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
        args=(run_id, run_dir, targets, embedding_host, int(embedding_port), ip_address),
        daemon=True,
        name="indexing-runner",
    )
    with _lock:
        _state.run_thread = worker
    worker.start()
    return get_indexing_overview()


def start_target_indexing(target_id: str, embedding_host: str = "localhost", embedding_port: int = 8000, ip_address: str = "localhost") -> dict[str, Any]:
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
    summary = _read_summary(run_dir)
    return {
        "main_log_tail": _tail(run_dir / "main.log", lines=tail_lines),
        "debug_log_tail": _tail(run_dir / "debug.log", lines=tail_lines),
        "summary": summary,
    }
