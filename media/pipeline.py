"""Media processing pipeline orchestrator.

Coordinates the 6-layer processing of media files:
L0 -> L1 -> L2 -> L3 -> L4 -> L5

Directory discovery is handled by the indexing service, which routes
media files here for rich processing.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from media.evidence_store import (
    _save_asset,
    get_asset,
    get_artifacts,
    infer_recorded_at_from_path,
    infer_recorded_day_from_path,
    list_assets,
    register_asset,
    _load_assets_index,
    save_artifact_bundle,
)
from media.event_extraction import (
    extract_events_from_scenes,
    extract_events_from_speech,
    merge_events,
)
from media.filtering import (
    filter_asset,
)
from media.memory import build_memory_from_recaps, build_memory_prompt
from media.models import (
    ComposedDocument,
    ContextualMemory,
    DerivedArtifact,
    LocalRecap,
    MediaAsset,
    Modality,
    OutputFormat,
    PipelineJob,
)
from media.recaps import build_recap_from_events, build_recaps, group_events_by_time_window
from media.composer import build_compose_prompt, compose_document, select_output_format
from media.text_cleanup import (
    build_readable_transcript_text,
    clean_transcript_segments,
    extract_inline_topic_terms,
    extract_topic_phrases,
    is_generic_topic_phrase,
    is_weak_topic_phrase,
    strip_summary_boilerplate,
)

logger = logging.getLogger("archivist.media.pipeline")

import shutil as _shutil
import threading as _threading

# Batch media (e.g. movie-library) processing is low priority: it must never
# starve real-time RTSP transcription for CPU, IO, or whisper workers. Cap how
# many media files process at once...
MEDIA_MAX_CONCURRENT_JOBS = max(1, int(os.getenv("MEDIA_MAX_CONCURRENT_JOBS", "2")))
_MEDIA_JOB_SEM = _threading.Semaphore(MEDIA_MAX_CONCURRENT_JOBS)

# ...and run the heavy ffmpeg decoders at low CPU/IO priority so the OS hands
# CPU/disk to the live pipeline first. Prefix is computed once at import.
def _lowpri_prefix() -> list[str]:
    pre: list[str] = []
    if os.getenv("MEDIA_BATCH_LOWPRI", "1").strip().lower() in {"1", "true", "yes", "on"}:
        if _shutil.which("nice"):
            pre += ["nice", "-n", "19"]
        if _shutil.which("ionice"):
            pre += ["ionice", "-c", "3"]
    return pre

LOWPRI_PREFIX = _lowpri_prefix()

PIPELINE_STORE_DIR = Path(os.getenv("MEDIA_PIPELINE_DIR", "/data/media_pipeline"))
MEDIA_PIPELINE_COMPAT_VERSION = os.getenv("MEDIA_PIPELINE_COMPAT_VERSION", "2026-04-11.1").strip() or "2026-04-11.1"
AGENT_EXECUTOR_URL = (
    os.getenv("ARCHIVIST_AGENT_EXECUTOR_URL")
    or os.getenv("ARCHIVIST_AGENT_CHAT_URL")
    or os.getenv("AGENT_EXECUTOR_URL")
    or ""
).strip().rstrip("/")
AGENT_EXECUTOR_TOKEN = (
    os.getenv("ARCHIVIST_AGENT_EXECUTOR_TOKEN")
    or os.getenv("ARCHIVIST_AGENT_CHAT_TOKEN")
    or os.getenv("AGENT_EXECUTOR_TOKEN")
    or ""
).strip()
AGENT_CHAT_MODEL = (os.getenv("ARCHIVIST_AGENT_CHAT_MODEL") or os.getenv("AGENT_CHAT_MODEL") or "").strip()
SUBJECT_MAX_WORDS = max(8, int(os.getenv("MEDIA_SUBJECT_MAX_WORDS", "24")))
SUBJECT_MAX_CONTEXT_ARTIFACTS = max(6, int(os.getenv("MEDIA_SUBJECT_MAX_CONTEXT_ARTIFACTS", "12")))
SUBJECT_MAX_PREVIEW_CHARS = max(80, int(os.getenv("MEDIA_SUBJECT_MAX_PREVIEW_CHARS", "220")))
SUBJECT_STOP_TERMS = {
    "additional", "are", "awesome", "blah", "everybody", "fuck", "god", "never",
    "no", "none", "nope", "obviously", "okay", "so", "they", "versus", "wait",
    "whereas", "yep", "yes",
}
SUBJECT_PARTICIPANT_STOP_TERMS = SUBJECT_STOP_TERMS | {
    "everybody", "everyone", "he", "i", "it", "me", "she", "team", "them",
    "us", "we", "you", "your",
}
SUBJECT_INVALID_PATTERNS = (
    r"^(and|but|or)\b",
    r"\bcurrent workstream\b",
    r"\bdiscussion focused\b",
    r"\bmain activity\b",
    r"\bopen questions around\b",
    r"\bsegment covers\b",
    r"\btalk about\b",
    r"\bthinking about\b",
    r"\band follow\b",
    r"\band and\b",
    r"\bthis window\b",
    r"^this (video|audio|media|recording) file\b",
)
PUBLIC_ARTIFACT_ORDER = {
    "subject_line": 0,
    "memory": 1,
    "document": 2,
    "transcript": 3,
}
PUBLIC_ARTIFACT_KINDS = set(PUBLIC_ARTIFACT_ORDER)


def _repo_root_path() -> Path:
    return Path(__file__).resolve().parents[1]


def _media_agent_id() -> str:
    for env_name in ("ARCHIVIST_MEDIA_AGENT_ID", "ARCHIVIST_AGENT_CONSOLE_AGENT_ID", "ARCHIVIST_CONSOLE_AGENT_ID"):
        value = os.getenv(env_name, "").strip()
        if value:
            return value
    return "operator-chat"


def _media_agent_model() -> str:
    if AGENT_CHAT_MODEL and not AGENT_CHAT_MODEL.endswith("/default"):
        return AGENT_CHAT_MODEL
    return f"agents/{_media_agent_id()}"


def _candidate_repo_roots() -> list[Path]:
    candidates = [
        os.getenv("ARCHIVIST_REPO_ROOT", "").strip(),
        str(_repo_root_path()),
        str(Path.cwd()),
        "/home/andy/archivist",
    ]
    seen: set[str] = set()
    roots: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        try:
            path = Path(candidate).expanduser().resolve()
        except OSError:
            continue
        path_text = str(path)
        if path_text in seen:
            continue
        seen.add(path_text)
        roots.append(path)
    return roots


def _resolve_git_dir(root: Path) -> Optional[Path]:
    git_entry = root / ".git"
    if git_entry.is_dir():
        return git_entry
    if not git_entry.is_file():
        return None
    try:
        raw = git_entry.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw.lower().startswith("gitdir:"):
        return None
    git_dir = raw.split(":", 1)[1].strip()
    if not git_dir:
        return None
    try:
        resolved = (root / git_dir).resolve() if not Path(git_dir).is_absolute() else Path(git_dir).resolve()
    except OSError:
        return None
    return resolved if resolved.exists() else None


def _read_git_ref_commit(git_dir: Path, ref_name: str) -> str:
    ref_path = git_dir / ref_name
    try:
        if ref_path.is_file():
            commit_hash = ref_path.read_text(encoding="utf-8").strip().lower()
            if re.fullmatch(r"[0-9a-f]{40}", commit_hash):
                return commit_hash
    except OSError:
        pass

    packed_refs = git_dir / "packed-refs"
    try:
        if packed_refs.is_file():
            for line in packed_refs.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("^"):
                    continue
                commit_hash, _, packed_ref = stripped.partition(" ")
                if packed_ref.strip() != ref_name:
                    continue
                commit_hash = commit_hash.strip().lower()
                if re.fullmatch(r"[0-9a-f]{40}", commit_hash):
                    return commit_hash
    except OSError:
        pass
    return ""


def _resolve_repo_commit_hash_from_git_files(root: Path) -> str:
    git_dir = _resolve_git_dir(root)
    if git_dir is None:
        return ""
    head_path = git_dir / "HEAD"
    try:
        head_value = head_path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if head_value.lower().startswith("ref:"):
        ref_name = head_value.split(":", 1)[1].strip()
        return _read_git_ref_commit(git_dir, ref_name)
    head_value = head_value.lower()
    return head_value if re.fullmatch(r"[0-9a-f]{40}", head_value) else ""


def _resolve_repo_commit_hash(repo_root: Optional[Path] = None) -> str:
    roots = [Path(repo_root).expanduser().resolve()] if repo_root is not None else _candidate_repo_roots()
    for root in roots:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            result = None
        if result is None or result.returncode != 0:
            commit_hash = _resolve_repo_commit_hash_from_git_files(root)
        else:
            commit_hash = str(result.stdout or "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{40}", commit_hash):
            return commit_hash
        commit_hash = _resolve_repo_commit_hash_from_git_files(root)
        if re.fullmatch(r"[0-9a-f]{40}", commit_hash):
            return commit_hash
    return ""


def _resolve_repo_version_tag(commit_hash: str, suffix_len: int = 12) -> str:
    normalized = str(commit_hash or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized):
        return ""
    width = max(6, int(suffix_len or 0))
    return normalized[-width:]


REPO_COMMIT_HASH = _resolve_repo_commit_hash()
REPO_VERSION_TAG = _resolve_repo_version_tag(REPO_COMMIT_HASH)
MEDIA_PIPELINE_VERSION = (
    os.getenv("MEDIA_PIPELINE_VERSION_TAG", "").strip()
    or os.getenv("MEDIA_PIPELINE_VERSION", "").strip()
    or REPO_VERSION_TAG
    or "unknown"
)

# ── Active job tracking ─────────────────────────────────────────────────

_active_jobs: dict[str, PipelineJob] = {}
_jobs_lock = threading.Lock()


def get_active_jobs() -> list[dict]:
    """Get all active/recent pipeline jobs."""
    with _jobs_lock:
        return [
            {
                "job_id": j.job_id,
                "media_id": j.media_id,
                "status": j.status,
                "current_layer": j.current_layer,
                "progress": j.progress,
                "started_at": j.started_at,
                "finished_at": j.finished_at,
                "error": j.error,
                "artifacts_count": j.artifacts_count,
                "events_count": j.events_count,
                "recaps_count": j.recaps_count,
            }
            for j in _active_jobs.values()
        ]


def _media_job_active(media_id: str) -> bool:
    with _jobs_lock:
        return any(
            job.media_id == media_id and not float(job.finished_at or 0.0)
            for job in _active_jobs.values()
        )


def _update_job(job: PipelineJob, **kwargs):
    for key, value in kwargs.items():
        setattr(job, key, value)


def _artifact_kind_counts(artifacts: list[DerivedArtifact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.kind] = counts.get(artifact.kind, 0) + 1
    return counts


def _public_artifact_sort_key(artifact: DerivedArtifact) -> tuple[int, float, float, str]:
    return (
        PUBLIC_ARTIFACT_ORDER.get(artifact.kind, 99),
        artifact.start_s,
        artifact.end_s,
        artifact.artifact_id,
    )


def _select_public_artifacts(artifacts: list[DerivedArtifact]) -> list[DerivedArtifact]:
    selected = [artifact for artifact in artifacts if artifact.kind in PUBLIC_ARTIFACT_KINDS]
    return sorted(selected, key=_public_artifact_sort_key)


def _sidecar_candidate_paths(asset_path: str | Path, suffix: str) -> list[Path]:
    path = Path(asset_path)
    return [
        path.with_suffix(suffix),
        path.with_name(f"{path.stem}.archivist{suffix}"),
        path.with_name(f"{path.name}.archivist{suffix}"),
    ]


def _sidecar_path_for_write(asset_path: str | Path, suffix: str) -> Path:
    for candidate in _sidecar_candidate_paths(asset_path, suffix):
        try:
            if not candidate.exists() or candidate.is_file():
                return candidate
        except OSError:
            continue
    return _sidecar_candidate_paths(asset_path, suffix)[-1]


def _existing_sidecar_path(asset_path: str | Path, suffix: str) -> Optional[Path]:
    for candidate in _sidecar_candidate_paths(asset_path, suffix):
        try:
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
        except OSError:
            continue
    return None


def _pipeline_sidecar_path(asset_path: str | Path) -> Path:
    return _sidecar_path_for_write(asset_path, ".json")


def _write_pipeline_sidecar(asset: MediaAsset, result: dict) -> Optional[Path]:
    sidecar_path = _pipeline_sidecar_path(asset.path)
    try:
        serializable = json.loads(json.dumps(result, default=str))
        sidecar_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        return sidecar_path
    except OSError as exc:
        logger.warning("Failed to write pipeline sidecar for %s: %s", asset.filename, exc)
        return None


def _media_output_complete(media_id: str) -> bool:
    return bool(media_id) and (PIPELINE_STORE_DIR / f"{media_id}.json").exists()


def _load_saved_pipeline_result(media_id: str) -> Optional[dict]:
    if not media_id:
        return None
    result_path = PIPELINE_STORE_DIR / f"{media_id}.json"
    if not result_path.exists():
        return None
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _current_source_mtime_ns(path: str | Path) -> Optional[int]:
    try:
        return int(Path(path).stat().st_mtime_ns)
    except OSError:
        return None


def _expected_output_format_label(output_format: Optional[OutputFormat]) -> Optional[str]:
    if output_format is None:
        return None
    return output_format.value if hasattr(output_format, "value") else str(output_format)


def _asset_result_payload(asset: MediaAsset) -> dict[str, object]:
    recorded_at = (
        str((asset.metadata or {}).get("recorded_at") or "").strip()
        or infer_recorded_at_from_path(asset.path)
        or ""
    )
    recorded_day = (
        str((asset.metadata or {}).get("recorded_day") or "").strip()
        or infer_recorded_day_from_path(asset.path)
        or ""
    )
    payload: dict[str, object] = {
        "path": asset.path,
        "filename": asset.filename,
        "modality": asset.modality.value,
        "duration_s": asset.duration_s,
        "file_hash": asset.file_hash,
    }
    if recorded_at:
        payload["recorded_at"] = recorded_at
    if recorded_day:
        payload["recorded_day"] = recorded_day
    return payload


def _build_pipeline_stamp(
    asset: MediaAsset,
    *,
    output_format: Optional[OutputFormat],
    document_format: Optional[str] = None,
    generated_at: Optional[float] = None,
) -> dict[str, object]:
    return {
        "pipeline_version": MEDIA_PIPELINE_VERSION,
        "pipeline_compat_version": MEDIA_PIPELINE_COMPAT_VERSION,
        "repo_commit": REPO_COMMIT_HASH,
        "repo_commit_suffix": REPO_VERSION_TAG or MEDIA_PIPELINE_VERSION,
        "source_path": asset.path,
        "source_file_hash": asset.file_hash,
        "source_size_bytes": int(asset.file_size_bytes or 0),
        "source_mtime_ns": _current_source_mtime_ns(asset.path),
        "source_recorded_at": (
            str((asset.metadata or {}).get("recorded_at") or "").strip()
            or infer_recorded_at_from_path(asset.path)
            or None
        ),
        "source_recorded_day": (
            str((asset.metadata or {}).get("recorded_day") or "").strip()
            or infer_recorded_day_from_path(asset.path)
            or None
        ),
        "requested_output_format": _expected_output_format_label(output_format),
        "document_format": document_format,
        "generated_at": float(generated_at or time.time()),
    }


def _result_has_pipeline_output(data: dict) -> bool:
    return bool(data.get("document") or data.get("transcript"))


def _looks_like_pipeline_result(data: dict) -> bool:
    return any(
        key in data
        for key in (
            "archivist_pipeline",
            "media_id",
            "asset",
            "document",
            "transcript",
            "layers",
            "artifacts",
            "job_id",
            "error",
        )
    )


def _legacy_pipeline_stamp_from_result(data: dict, result_file: Path) -> dict[str, object]:
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    source_path = str(asset.get("path") or "").strip()
    source_size = asset.get("file_size_bytes") or asset.get("size_bytes") or asset.get("bytes") or 0
    try:
        source_size_int = int(source_size or 0)
    except (TypeError, ValueError):
        source_size_int = 0
    try:
        generated_at = float(result_file.stat().st_mtime)
    except OSError:
        generated_at = time.time()
    document = data.get("document") if isinstance(data.get("document"), dict) else {}
    return {
        "pipeline_version": MEDIA_PIPELINE_VERSION,
        "pipeline_compat_version": MEDIA_PIPELINE_COMPAT_VERSION,
        "repo_commit": REPO_COMMIT_HASH,
        "repo_commit_suffix": REPO_VERSION_TAG or MEDIA_PIPELINE_VERSION,
        "source_path": source_path,
        "source_file_hash": str(asset.get("file_hash") or "").strip(),
        "source_size_bytes": source_size_int,
        "source_mtime_ns": None,
        "source_recorded_at": str(asset.get("recorded_at") or "").strip() or infer_recorded_at_from_path(source_path) or None,
        "source_recorded_day": str(asset.get("recorded_day") or "").strip() or infer_recorded_day_from_path(source_path) or None,
        "requested_output_format": None,
        "document_format": str(document.get("format") or "").strip() or None,
        "generated_at": generated_at,
        "legacy_result": True,
    }


def _refresh_asset_state_from_disk(asset: MediaAsset) -> MediaAsset:
    stat = Path(asset.path).stat()
    asset.file_size_bytes = int(stat.st_size)
    asset.file_hash = asset.compute_hash()
    asset.indexed_at = time.time()
    _save_asset(asset)
    return asset


def _expected_vectorstore_source_id(media_id: str) -> str:
    return f"media:{media_id}"


def _vectorstore_layer_is_current(
    result: Optional[dict],
    *,
    media_id: str,
    asset_file_hash: Optional[str],
) -> bool:
    if not isinstance(result, dict):
        return False
    layers = result.get("layers")
    if not isinstance(layers, dict):
        return False
    stats = layers.get("L6_vectorstore")
    if not isinstance(stats, dict) or stats.get("error"):
        return False

    chunks_created = int(stats.get("chunks_created") or 0)
    chunks_inserted = int(stats.get("chunks_inserted") or 0)
    if chunks_created <= 0 or chunks_inserted != chunks_created:
        return False

    if str(stats.get("collection") or "") != "documents_transcripts":
        return False
    if str(stats.get("source_id") or "") != _expected_vectorstore_source_id(media_id):
        return False
    if asset_file_hash and str(stats.get("file_hash") or "") != asset_file_hash:
        return False
    return True


def _embedded_processing_stamp_text(pipeline_stamp: dict[str, object]) -> str:
    hash_text = str(pipeline_stamp.get("source_file_hash") or "").strip()
    hash_preview = hash_text[:12] if hash_text else "unknown"
    version_tag = str(
        pipeline_stamp.get("repo_commit_suffix")
        or pipeline_stamp.get("pipeline_version")
        or "unknown"
    ).strip()
    compat_version = str(
        pipeline_stamp.get("pipeline_compat_version")
        or "unknown"
    ).strip()
    format_label = str(
        pipeline_stamp.get("document_format")
        or pipeline_stamp.get("requested_output_format")
        or "auto"
    ).strip()
    source_mtime_ns = pipeline_stamp.get("source_mtime_ns")
    return (
        f"Archivist pipeline {version_tag}"
        f" | compat={compat_version}"
        f" | format={format_label}"
        f" | hash={hash_preview}"
        f" | mtime_ns={source_mtime_ns if source_mtime_ns is not None else 'unknown'}"
    )


def _pipeline_result_is_current(
    result: Optional[dict],
    *,
    asset_path: str,
    asset_file_hash: Optional[str] = None,
    asset_file_size_bytes: Optional[int] = None,
    requested_output_format: Optional[OutputFormat] = None,
) -> bool:
    if not isinstance(result, dict) or result.get("error"):
        return False

    stamp = result.get("archivist_pipeline")
    if not isinstance(stamp, dict):
        return False

    stamped_compat_version = str(stamp.get("pipeline_compat_version") or "").strip()
    if stamped_compat_version:
        if stamped_compat_version != MEDIA_PIPELINE_COMPAT_VERSION:
            return False
    elif str(stamp.get("pipeline_version") or "").strip() != MEDIA_PIPELINE_COMPAT_VERSION:
        return False

    resolved_path = str(Path(asset_path).resolve())
    if str(stamp.get("source_path") or "") != resolved_path:
        return False

    current_mtime_ns = _current_source_mtime_ns(resolved_path)
    stamped_mtime_ns = stamp.get("source_mtime_ns")
    if current_mtime_ns is None or stamped_mtime_ns is None or int(stamped_mtime_ns) != current_mtime_ns:
        return False

    if asset_file_size_bytes is not None:
        stamped_size = stamp.get("source_size_bytes")
        if stamped_size is None or int(stamped_size) != int(asset_file_size_bytes):
            return False

    if asset_file_hash:
        if str(stamp.get("source_file_hash") or "") != asset_file_hash:
            return False

    expected_format = _expected_output_format_label(requested_output_format)
    if expected_format:
        existing_format = str(
            stamp.get("document_format")
            or ((result.get("document") or {}).get("format") if isinstance(result.get("document"), dict) else "")
            or ""
        )
        if existing_format != expected_format:
            return False

    return True


def _asset_record_complete(asset_data: dict) -> bool:
    path = str(asset_data.get("path") or "")
    media_id = str(asset_data.get("media_id") or "")
    if not path or not media_id or not Path(path).exists() or not _media_output_complete(media_id):
        return False
    result = _load_saved_pipeline_result(media_id)
    pipeline_current = _pipeline_result_is_current(
        result,
        asset_path=path,
        asset_file_hash=str(asset_data.get("file_hash") or "") or None,
        asset_file_size_bytes=int(asset_data.get("file_size_bytes") or 0) or None,
    )
    if not pipeline_current:
        return False
    return _vectorstore_layer_is_current(
        result,
        media_id=media_id,
        asset_file_hash=str(asset_data.get("file_hash") or "") or None,
    )


def _clip_subject_text(text: str, limit: int = SUBJECT_MAX_PREVIEW_CHARS) -> str:
    clean = " ".join(str(text or "").split()).strip()
    if len(clean) <= limit:
        return clean
    clipped = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def _subject_artifact_priority(kind: str) -> int:
    priority = {
        "document": 0,
        "memory": 1,
        "recap": 2,
        "event": 3,
        "transcript": 4,
        "scene": 5,
        "speech_segment": 6,
        "keyframe": 7,
    }
    return priority.get(kind, 99)


def _join_subject_terms(values: list[str], limit: int = 3) -> str:
    cleaned = _clean_subject_terms(values, limit=limit)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _clean_subject_terms(values: list[str], limit: Optional[int] = None) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        term = strip_summary_boilerplate(_clip_subject_text(value, limit=80)).strip(" ,.;:-")
        if not term or term.lower() in SUBJECT_STOP_TERMS or is_generic_topic_phrase(term) or is_weak_topic_phrase(term):
            continue
        if term not in cleaned:
            cleaned.append(term)
        if limit is not None and len(cleaned) >= limit:
            break
    return cleaned


def _is_subject_participant(value: str) -> bool:
    candidate = " ".join(str(value or "").split()).strip(" ,.;:-")
    if not candidate or candidate.isupper():
        return False
    parts = [part.strip(" ,.;:-") for part in candidate.split() if part.strip(" ,.;:-")]
    if not parts or len(parts) > 3:
        return False
    if any(not part[:1].isupper() for part in parts):
        return False
    lowered = [part.lower() for part in parts]
    if any(part in SUBJECT_PARTICIPANT_STOP_TERMS for part in lowered):
        return False
    if len(parts) == 1 and len(parts[0]) <= 1:
        return False
    return True


def _clean_subject_participants(values: list[str], limit: Optional[int] = None) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        candidate = _clip_subject_text(value, limit=80).strip(" ,.;:-")
        if not _is_subject_participant(candidate):
            continue
        if candidate not in cleaned:
            cleaned.append(candidate)
        if limit is not None and len(cleaned) >= limit:
            break
    return cleaned


def _join_subject_participants(values: list[str], limit: int = 3) -> str:
    cleaned = _clean_subject_participants(values, limit=limit)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _subject_noun(document: Optional[ComposedDocument]) -> str:
    if document and document.format == OutputFormat.MEETING_MINUTES:
        return "Meeting"
    if document and document.format == OutputFormat.INCIDENT_REPORT:
        return "Incident review"
    if document and document.format == OutputFormat.EXECUTIVE_BRIEF:
        return "Briefing"
    return "Discussion"


def _infer_subject_activity(artifacts: list[DerivedArtifact], document: Optional[ComposedDocument]) -> str:
    event_type_counts: dict[str, int] = {}
    for artifact in artifacts:
        if artifact.kind != "event":
            continue
        label = str(artifact.metadata.get("event_type") or "").strip().lower()
        if label:
            event_type_counts[label] = event_type_counts.get(label, 0) + 1

    if event_type_counts.get("decision") and event_type_counts.get("question"):
        return "covers decisions and open questions"
    if event_type_counts.get("decision") and event_type_counts.get("action"):
        return "covers decisions and follow-up work"
    if event_type_counts.get("decision"):
        return "reaches concrete decisions"
    if event_type_counts.get("question"):
        return "surfaces open questions"
    if event_type_counts.get("action"):
        return "tracks follow-up work"
    if document and document.format == OutputFormat.MEETING_MINUTES:
        return "covers the main discussion"
    if document and document.format == OutputFormat.INCIDENT_REPORT:
        return "documents the incident review"
    if document and document.format == OutputFormat.EXECUTIVE_BRIEF:
        return "captures the main points"
    return "captures the main developments"


def _subject_topic(memory: ContextualMemory, artifacts: list[DerivedArtifact], document: Optional[ComposedDocument]) -> str:
    direct_candidates = _clean_subject_terms(memory.inferred_themes, limit=3)
    if direct_candidates:
        return _join_subject_terms(direct_candidates, limit=3)

    source_texts: list[str] = []
    if memory.context_overview:
        source_texts.append(memory.context_overview)
    for takeaway in memory.final_takeaways[:4]:
        source_texts.append(takeaway)
    if document:
        for section in document.sections:
            content = str(section.get("content") or "").strip()
            if content:
                source_texts.append(content)
    for artifact in sorted(
        artifacts,
        key=lambda artifact: (_subject_artifact_priority(artifact.kind), artifact.start_s, artifact.end_s),
    ):
        if artifact.kind == "event":
            source_texts.append(str(artifact.metadata.get("brief") or artifact.content))
            source_texts.extend(str(entity) for entity in artifact.metadata.get("entities", []) or [])
            source_texts.extend(str(term) for term in artifact.metadata.get("topic_terms", []) or [])
        elif artifact.kind == "recap":
            source_texts.append(str(artifact.metadata.get("window_summary") or artifact.content))
        if len(source_texts) >= 16:
            break

    extracted = _clean_subject_terms(extract_topic_phrases(source_texts, limit=4), limit=3)
    if extracted:
        return _join_subject_terms(extracted, limit=3)

    inline_terms = _clean_subject_terms([
        term
        for text in source_texts
        for term in extract_inline_topic_terms(text, limit=3)
    ], limit=3)
    if inline_terms:
        return _join_subject_terms(inline_terms, limit=3)

    for text in source_texts:
        candidate = strip_summary_boilerplate(str(text or "")).strip(" .")
        if not candidate or is_generic_topic_phrase(candidate) or is_weak_topic_phrase(candidate):
            continue
        first_sentence = candidate.split(".", 1)[0].strip()
        if re.search(r"\b(i|we|they|he|she|it|this|that)\b", first_sentence, re.IGNORECASE):
            continue
        if 2 <= len(first_sentence.split()) <= 6:
            return first_sentence
    return ""


def _subject_line_is_unusable(text: str) -> bool:
    clean = " ".join(str(text or "").split()).strip(" .")
    if len(clean.split()) < 4:
        return True
    return any(re.search(pattern, clean, re.IGNORECASE) for pattern in SUBJECT_INVALID_PATTERNS)


def _resolve_agent_executor_token() -> str:
    if AGENT_EXECUTOR_TOKEN:
        return AGENT_EXECUTOR_TOKEN
    return ""


def _call_agent_executor(
    *,
    asset: MediaAsset,
    system_prompt: str,
    user_prompt: str,
    purpose: str,
    timeout: int = 120,
) -> tuple[str, Optional[str]]:
    token = _resolve_agent_executor_token()
    if not token or not AGENT_EXECUTOR_URL:
        return "", "executor_unconfigured"

    try:
        import requests

        agent_id = _media_agent_id()
        session_key = f"agent:{agent_id}:{purpose}:{asset.media_id}"

        response = requests.post(
            f"{AGENT_EXECUTOR_URL}/v1/chat/completions",
            json={
                "model": _media_agent_model(),
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "user": session_key,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-agent-id": agent_id,
                "x-agent-session-key": session_key,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = str(payload.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        return content, None
    except Exception as exc:
        logger.warning("%s inference failed for %s: %s", purpose, asset.filename, exc)
        return "", str(exc)


def _subject_event_summary(artifacts: list[DerivedArtifact]) -> str:
    event_priority = {"decision": 0, "action": 1, "question": 2, "observation": 3, "speech": 4}
    ranked = sorted(
        [
            artifact
            for artifact in artifacts
            if artifact.kind == "event" and str(artifact.metadata.get("event_type") or "").strip()
        ],
        key=lambda artifact: (
            event_priority.get(str(artifact.metadata.get("event_type") or "").strip().lower(), 9),
            artifact.start_s,
            artifact.end_s,
        ),
    )

    for artifact in ranked:
        event_type = str(artifact.metadata.get("event_type") or "").strip().lower()
        brief = strip_summary_boilerplate(str(artifact.metadata.get("brief") or artifact.content)).strip(" .")
        if not brief or is_generic_topic_phrase(brief):
            continue
        if event_type == "decision":
            match = re.match(r"^(?:we|i)\s+decid(?:e|ed)\s+to\s+(.+)$", brief, re.IGNORECASE)
            if match:
                candidate = f"Decision to {match.group(1).strip(' .')}"
            else:
                candidate = f"Decision: {brief}"
        elif event_type == "action":
            match = re.match(r"^(?:i(?:'ll| will)|we(?:'ll| will)|let me)\s+(.+)$", brief, re.IGNORECASE)
            if match:
                candidate = f"Follow-up: {match.group(1).strip(' .')}"
            else:
                candidate = f"Follow-up: {brief}"
        elif event_type == "question":
            candidate = f"Open question: {brief.rstrip('?')}"
        else:
            candidate = brief

        if candidate and not _subject_line_is_unusable(candidate):
            return candidate
    return ""


def _build_subject_line_fallback(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> str:
    participants = _join_subject_participants(memory.main_actors, limit=2)
    topic = _subject_topic(memory, artifacts, document)

    entities: list[str] = []
    for artifact in artifacts:
        if artifact.kind == "event":
            source_entities = artifact.metadata.get("entities", []) or []
        elif artifact.kind == "recap":
            source_entities = artifact.metadata.get("salient_entities", []) or []
        else:
            source_entities = []
        for entity in source_entities:
            entity_text = str(entity or "").strip()
            if entity_text and entity_text not in entities:
                entities.append(entity_text)
        if len(entities) >= 3:
            break
    entity_text = _join_subject_terms(entities, limit=2)

    activity = _infer_subject_activity(artifacts, document)
    subject_noun = _subject_noun(document)
    event_summary = _subject_event_summary(artifacts)

    if topic:
        return f"{subject_noun} on {topic} {activity}."
    if event_summary:
        return f"{event_summary}."
    if entity_text:
        return f"{subject_noun} involving {entity_text} {activity}."
    if participants:
        return f"{participants} lead a {subject_noun.lower()} that {activity}."
    if document and document.title:
        title_text = _clip_subject_text(document.title, limit=100).strip(" .")
        return f"{subject_noun} documents {title_text.lower()}."
    return f"The recording {activity}."


def _normalize_subject_line(text: str, fallback: str) -> str:
    clean = str(text or "").strip()
    clean = clean.replace("\r", " ")
    clean = clean.splitlines()[0].strip() if clean else ""
    clean = clean.removeprefix("Subject:").removeprefix("subject:").strip()
    clean = clean.strip("`\"' ")
    if not clean:
        clean = fallback
    clean = " ".join(clean.split()).strip()

    split = clean.replace("!", ".").replace("?", ".")
    first_sentence = split.split(".", 1)[0].strip()
    clean = first_sentence or clean

    words = clean.split()
    if len(words) > SUBJECT_MAX_WORDS:
        clean = " ".join(words[:SUBJECT_MAX_WORDS]).rstrip(" ,;:-")

    if _subject_line_is_unusable(clean):
        clean = fallback

    if clean and clean[-1] not in ".!?":
        clean = f"{clean}."
    return clean or fallback


def build_subject_line_prompt(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> tuple[str, str, list[str]]:
    kind_counts: dict[str, int] = {}
    for artifact in artifacts:
        kind_counts[artifact.kind] = kind_counts.get(artifact.kind, 0) + 1

    selected = sorted(
        artifacts,
        key=lambda artifact: (_subject_artifact_priority(artifact.kind), artifact.start_s, artifact.end_s),
    )[:SUBJECT_MAX_CONTEXT_ARTIFACTS]

    context_lines = []
    source_refs: list[str] = []
    for artifact in selected:
        preview = _clip_subject_text(artifact.content)
        if artifact.kind == "event":
            event_type = str(artifact.metadata.get("event_type") or "event")
            preview = f"{event_type}: {preview}"
        elif artifact.kind == "recap":
            preview = f"window {artifact.start_s:.0f}-{artifact.end_s:.0f}s: {preview}"
        elif artifact.kind == "memory":
            preview = (
                f"actors={', '.join(memory.main_actors[:5]) or 'none'}; "
                f"themes={', '.join(memory.inferred_themes[:5]) or 'none'}"
            )
        elif artifact.kind == "document":
            preview = _clip_subject_text(document.full_text if document else artifact.content)
        context_lines.append(f"- [{artifact.kind}] {preview}")
        source_refs.append(artifact.artifact_id)

    topic = _subject_topic(memory, artifacts, document)
    summary_lines = [
        f"Filename: {asset.filename}",
        f"Modality: {asset.modality.value}",
        f"Duration seconds: {asset.duration_s:.1f}",
        f"Document format: {document.format.value if document and hasattr(document.format, 'value') else ''}",
        f"Main actors: {', '.join(memory.main_actors[:6]) or 'none'}",
        f"Themes: {', '.join(memory.inferred_themes[:6]) or 'none'}",
        f"Best topic candidate: {topic or 'none'}",
        f"Open loops: {len(memory.open_loops)}",
        "Artifact counts: " + ", ".join(f"{kind}={count}" for kind, count in sorted(kind_counts.items())),
        "Representative artifacts:",
        *(context_lines or ["- [none] no artifact context available"]),
        "",
        f"Write one factual sentence only, under {SUBJECT_MAX_WORDS} words, describing what the recording is about.",
        "Write like a professional editor: specific, clean, and complete.",
        "Lead with the topic, not with a file label or a speaker list.",
        "Avoid vague phrasing such as current workstream, main activity, discussion focused, and open questions around.",
        "Do not begin with conjunctions like And/But/Or.",
        "Mention people only when they are clearly relevant and confidently identified.",
    ]
    system_prompt = (
        "You create concise archival subject lines for processed media files. "
        "Return exactly one sentence with no markdown, no quotes, no file IDs, and no speaker labels unless they are essential to understanding the topic."
    )
    return system_prompt, "\n".join(summary_lines), source_refs


def _generate_subject_line(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> tuple[str, dict]:
    fallback = _build_subject_line_fallback(asset, artifacts, memory, document)
    system_prompt, user_prompt, source_refs = build_subject_line_prompt(asset, artifacts, memory, document)
    details = {
        "generator": "heuristic",
        "model": None,
        "source_artifact_count": len(artifacts),
        "context_artifact_refs": source_refs,
        "error": None,
    }

    if not _resolve_agent_executor_token() or not AGENT_EXECUTOR_URL:
        return _normalize_subject_line(fallback, fallback), details | {"reason": "executor_unconfigured"}

    try:
        content, error = _call_agent_executor(
            asset=asset,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            purpose="media-subject",
            timeout=90,
        )
        if error:
            raise RuntimeError(error)
        subject_line = _normalize_subject_line(content, fallback)
        return subject_line, details | {"generator": "agent-executor", "model": _media_agent_model()}
    except Exception as exc:
        logger.warning("Subject line inference failed for %s: %s", asset.filename, exc)
        return _normalize_subject_line(fallback, fallback), details | {
            "reason": "executor_error",
            "error": str(exc),
            "model": _media_agent_model(),
        }


def _compose_document_via_agent_executor(
    asset: MediaAsset,
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list,
    output_format: OutputFormat,
) -> Optional[ComposedDocument]:
    if not _resolve_agent_executor_token() or not AGENT_EXECUTOR_URL:
        return None

    system_prompt, user_prompt = build_compose_prompt(memory, recaps, events, output_format)
    user_prompt = (
        f"{user_prompt}\n\n"
        "## Output constraints\n"
        "Return markdown only.\n"
        "Use the exact requested section headings.\n"
        "Write like a professional technical writer: clear, relevant, concrete, and concise.\n"
        "Do not invent participants, decisions, or follow-up work.\n"
        "Avoid filler, hedging, and repetitive phrasing.\n"
    )
    content, error = _call_agent_executor(
        asset=asset,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        purpose="media-compose",
        timeout=180,
    )
    if error or not content or "## " not in content:
        return None
    try:
        return compose_document(memory, recaps, events, output_format=output_format, composed_text=content)
    except Exception:
        logger.warning("Failed to parse composed markdown for %s", asset.filename)
        return None


def _backfill_memory_from_document(memory: ContextualMemory, document: Optional[ComposedDocument]) -> ContextualMemory:
    if not document or not document.sections:
        return memory

    context_section = next((section for section in document.sections if str(section.get("heading") or "").strip().lower() == "context overview"), None)
    topic_section = next((section for section in document.sections if str(section.get("heading") or "").strip().lower() == "key topics"), None)

    if context_section:
        paragraphs = [part.strip() for part in str(context_section.get("content") or "").split("\n\n") if part.strip()]
        if paragraphs:
            memory.context_overview = paragraphs[0]

    if topic_section:
        topics: list[str] = []
        for line in str(topic_section.get("content") or "").splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            topic = re.sub(r"^\-\s*(?:\[[^\]]+\]\s*)?", "", stripped).strip()
            topic = strip_summary_boilerplate(topic).strip(" .")
            if not topic or is_weak_topic_phrase(topic) or is_generic_topic_phrase(topic):
                continue
            if topic not in topics:
                topics.append(topic)
            if len(topics) >= 6:
                break
        if topics:
            memory.inferred_themes = topics

    return memory


# ── Pipeline Execution ──────────────────────────────────────────────────


def process_media_file(
    path: str,
    output_format: Optional[OutputFormat] = None,
    recap_window_s: float = 60.0,
    metadata: Optional[dict] = None,
    force_reprocess: bool = False,
) -> dict:
    """Bounded entry point for media processing.

    Acquires a global semaphore so at most MEDIA_MAX_CONCURRENT_JOBS files
    process concurrently — keeps batch (movie-library) work from starving
    real-time RTSP transcription. Waiting callers block here cheaply.
    """
    with _MEDIA_JOB_SEM:
        return _process_media_file_impl(
            path,
            output_format=output_format,
            recap_window_s=recap_window_s,
            metadata=metadata,
            force_reprocess=force_reprocess,
        )


def _process_media_file_impl(
    path: str,
    output_format: Optional[OutputFormat] = None,
    recap_window_s: float = 60.0,
    metadata: Optional[dict] = None,
    force_reprocess: bool = False,
) -> dict:
    """Process a single media file through the full pipeline.

    Returns a dict with results from each layer.

    Args:
        path: Path to the media file.
        output_format: Desired output format. Auto-detected if None.
        recap_window_s: Time window for grouping events into recaps.
        metadata: Optional metadata to attach to the asset.
    """
    job = PipelineJob(started_at=time.time())
    with _jobs_lock:
        _active_jobs[job.job_id] = job

    result: dict = {"job_id": job.job_id, "layers": {}}

    try:
        # ── L0: Register asset ──────────────────────────────────────
        _update_job(job, status="deriving", current_layer="L0_evidence", progress=0.1)
        asset = register_asset(path, metadata=metadata)
        job.media_id = asset.media_id
        result["media_id"] = asset.media_id
        result["asset"] = _asset_result_payload(asset)

        if not force_reprocess:
            existing_result = _load_saved_pipeline_result(asset.media_id)
            pipeline_current = _pipeline_result_is_current(
                existing_result,
                asset_path=asset.path,
                asset_file_hash=asset.file_hash,
                asset_file_size_bytes=asset.file_size_bytes,
                requested_output_format=output_format,
            )
            if pipeline_current:
                if not _vectorstore_layer_is_current(
                    existing_result,
                    media_id=asset.media_id,
                    asset_file_hash=asset.file_hash,
                ):
                    backfill_stats = _backfill_saved_vectorstore_projection(asset, existing_result)
                    if isinstance(existing_result, dict):
                        layers = dict(existing_result.get("layers") or {})
                        layers["L6_vectorstore"] = backfill_stats
                        existing_result["layers"] = layers

                if _vectorstore_layer_is_current(
                    existing_result,
                    media_id=asset.media_id,
                    asset_file_hash=asset.file_hash,
                ):
                    reused_result = dict(existing_result)
                    reused_result["job_id"] = job.job_id
                    reused_result["reused_existing_result"] = True
                    reused_result["skip_reason"] = "current_pipeline_result"
                    reused_result["asset"] = _asset_result_payload(asset)
                    _update_job(job, status="done", current_layer="", progress=1.0, finished_at=time.time())
                    logger.info("Skipping unchanged media file %s; current pipeline result already exists", asset.filename)
                    return reused_result

        # ── Derive transcription for audio/video ────────────────────
        transcript_payload = None
        transcript_segments = None
        if asset.modality in (Modality.AUDIO, Modality.VIDEO):
            transcript_payload = _derive_transcript(asset, job)
            transcript_segments = transcript_payload.get("segments") if transcript_payload else None
        if transcript_payload:
            result["transcript"] = {
                "text": transcript_payload.get("text", ""),
                "meta": transcript_payload.get("meta", {}),
                "segment_count": len(transcript_segments or []),
                "vtt_text": _build_transcript_vtt_text(asset, transcript_payload),
            }

        # ── L1: Filter ──────────────────────────────────────────────
        _update_job(job, status="filtering", current_layer="L1_filtering", progress=0.3)
        filter_results = filter_asset(asset, transcript_segments=transcript_segments)
        result["layers"]["L1_filtering"] = {
            "scene_count": len(filter_results.get("scenes", [])),
            "speech_segment_count": len(filter_results.get("speech_segments", [])),
            "keyframe_count": len(filter_results.get("keyframes", [])),
        }

        # ── L2: Extract events ──────────────────────────────────────
        _update_job(job, status="extracting", current_layer="L2_events", progress=0.5)
        speech_events = extract_events_from_speech(
            filter_results.get("speech_segments", []),
            media_id=asset.media_id,
        )
        scene_events = extract_events_from_scenes(
            filter_results.get("scenes", []),
            media_id=asset.media_id,
        )
        all_events = merge_events(speech_events, scene_events)
        job.events_count = len(all_events)
        result["layers"]["L2_events"] = {
            "total_events": len(all_events),
            "speech_events": len(speech_events),
            "scene_events": len(scene_events),
        }

        # ── L3: Build recaps ───────────────────────────────────────
        _update_job(job, status="recapping", current_layer="L3_recaps", progress=0.7)
        recaps = build_recaps(all_events, window_s=recap_window_s)
        job.recaps_count = len(recaps)
        result["layers"]["L3_recaps"] = {
            "recap_count": len(recaps),
            "ledger_entry_count": sum(len(recap.ledger_entries) for recap in recaps),
        }

        # ── L4: Build memory ───────────────────────────────────────
        _update_job(job, status="memorizing", current_layer="L4_memory", progress=0.85)
        memory = build_memory_from_recaps(recaps, media_id=asset.media_id, events=all_events)
        result["layers"]["L4_memory"] = {
            "context_overview": memory.context_overview,
            "main_actors": memory.main_actors,
            "themes": memory.inferred_themes,
            "open_loops_count": len(memory.open_loops),
            "evidence_map_keys": sorted(memory.evidence_map.keys()),
        }

        # ── L5: Compose document ───────────────────────────────────
        _update_job(job, status="composing", current_layer="L5_compose", progress=0.95)
        if output_format is None:
            output_format = select_output_format(memory, all_events)

        document = compose_document(memory, recaps, all_events, output_format=output_format)
        llm_document = _compose_document_via_agent_executor(asset, memory, recaps, all_events, output_format)
        if llm_document is not None:
            document = llm_document
            memory = _backfill_memory_from_document(memory, document)
            result["layers"]["L4_memory"] = {
                "context_overview": memory.context_overview,
                "main_actors": memory.main_actors,
                "themes": memory.inferred_themes,
                "open_loops_count": len(memory.open_loops),
                "evidence_map_keys": sorted(memory.evidence_map.keys()),
            }
        result["layers"]["L5_compose"] = {
            "format": document.format.value,
            "title": document.title,
            "section_count": len(document.sections),
            "text_length": len(document.full_text),
        }
        result["document"] = {
            "format": document.format.value,
            "title": document.title,
            "full_text": document.full_text,
            "sections": document.sections,
        }

        # ── Build and persist canonical artifact bundle ────────────
        trace_artifacts = _build_layer_artifacts(
            asset,
            transcript_payload,
            filter_results,
            all_events,
            recaps,
            memory,
            document,
            job,
        )

        # Store prompts for optional LLM enhancement
        result["prompts"] = {}
        if recaps:
            from media.recaps import build_recap_prompt
            sys_p, user_p = build_recap_prompt(all_events[:20])
            result["prompts"]["recap_sample"] = {"system": sys_p, "user": user_p}

        if recaps:
            mem_sys, mem_user = build_memory_prompt(recaps, media_id=asset.media_id)
            result["prompts"]["memory"] = {"system": mem_sys, "user": mem_user}

        comp_sys, comp_user = build_compose_prompt(memory, recaps, all_events, output_format)
        result["prompts"]["compose"] = {"system": comp_sys, "user": comp_user}

        # ── Final subject line inference ───────────────────────────
        _update_job(job, status="summarizing", current_layer="L7_subject_line", progress=0.98)
        subject_sys, subject_user, _ = build_subject_line_prompt(asset, trace_artifacts, memory, document)
        result["prompts"]["subject_line"] = {"system": subject_sys, "user": subject_user}
        subject_line, subject_details = _generate_subject_line(asset, trace_artifacts, memory, document)
        result["subject_line"] = subject_line
        result["document"]["subject_line"] = subject_line
        result["layers"]["L7_subject_line"] = {
            "subject_line": subject_line,
            **subject_details,
        }
        trace_artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="subject_line",
            start_s=0.0,
            end_s=asset.duration_s,
            content=subject_line,
            confidence=1.0 if subject_details.get("generator") == "agent-executor" else 0.7,
            metadata={
                "layer": "L7",
                "generator": subject_details.get("generator"),
                "model": subject_details.get("model"),
                "source_artifact_count": subject_details.get("source_artifact_count"),
            },
            source_refs=subject_details.get("context_artifact_refs", []),
        ))
        trace_artifacts.sort(key=lambda artifact: (artifact.start_s, artifact.end_s, artifact.kind, artifact.artifact_id))
        public_artifacts = _select_public_artifacts(trace_artifacts)
        pipeline_stamp = _build_pipeline_stamp(
            asset,
            output_format=output_format,
            document_format=document.format.value if hasattr(document.format, "value") else str(document.format),
        )
        result["archivist_pipeline"] = pipeline_stamp
        result["document"]["archivist_pipeline"] = pipeline_stamp
        result["artifacts"] = [_artifact_to_dict(artifact) for artifact in public_artifacts]
        result["artifact_count"] = len(public_artifacts)
        result["trace_artifact_count"] = len(trace_artifacts)
        result["trace_artifact_counts"] = _artifact_kind_counts(trace_artifacts)
        job.artifacts_count = len(public_artifacts)
        save_artifact_bundle(
            asset.media_id,
            trace_artifacts,
            bundle_metadata={"archivist_pipeline": pipeline_stamp},
        )

        # Persist the canonical result before embedding it into the media file.
        result_path = _save_pipeline_result(asset.media_id, result)
        result["artifact_bundle_path"] = str(result_path)
        sidecar_path = _write_pipeline_sidecar(asset, result)
        if sidecar_path is not None:
            result["artifact_bundle_sidecar_path"] = str(sidecar_path)

        # ── Inject metadata into source file ───────────────────────
        result["injection"] = _inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=transcript_payload,
            result_path=sidecar_path or result_path,
            subject_line=result.get("subject_line"),
            pipeline_stamp=pipeline_stamp,
        )
        asset = _refresh_asset_state_from_disk(asset)
        result["asset"] = _asset_result_payload(asset)
        final_pipeline_stamp = _build_pipeline_stamp(
            asset,
            output_format=output_format,
            document_format=document.format.value if hasattr(document.format, "value") else str(document.format),
            generated_at=pipeline_stamp.get("generated_at") if isinstance(pipeline_stamp, dict) else None,
        )
        result["archivist_pipeline"] = final_pipeline_stamp
        result["document"]["archivist_pipeline"] = final_pipeline_stamp
        save_artifact_bundle(
            asset.media_id,
            trace_artifacts,
            bundle_metadata={"archivist_pipeline": final_pipeline_stamp},
        )
        if transcript_payload:
            refreshed_vtt_path = _write_transcript_sidecar(asset, transcript_payload, pipeline_stamp=final_pipeline_stamp)
            if refreshed_vtt_path is not None:
                result["injection"]["transcript_sidecar_path"] = str(refreshed_vtt_path)

        # ── L6: Vectorstore projection ─────────────────────────────
        # Insert transcript chunks into Milvus after metadata embedding so the
        # stored file hash matches the final on-disk asset state.
        _update_job(job, status="indexing", current_layer="L6_vectorstore", progress=0.99)
        result["layers"]["L6_vectorstore"] = _insert_trace_artifacts_into_vectorstore(asset, trace_artifacts)
        _save_pipeline_result(asset.media_id, result)
        if sidecar_path is not None:
            _write_pipeline_sidecar(asset, result)

        # ── Done ───────────────────────────────────────────────────
        _update_job(job, status="done", current_layer="", progress=1.0, finished_at=time.time())

        logger.info(
            "Pipeline complete for %s: %d events, %d recaps, format=%s",
            asset.filename, len(all_events), len(recaps), output_format.value,
        )

    except Exception as e:
        _update_job(job, status="error", error=str(e), finished_at=time.time())
        result["error"] = str(e)
        logger.exception("Pipeline failed for %s", path)

    return result


def _artifact_to_dict(artifact: DerivedArtifact) -> dict:
    return {
        "artifact_id": artifact.artifact_id,
        "media_id": artifact.media_id,
        "kind": artifact.kind,
        "start_s": artifact.start_s,
        "end_s": artifact.end_s,
        "content": artifact.content,
        "confidence": artifact.confidence,
        "metadata": artifact.metadata,
        "source_refs": artifact.source_refs,
    }


def _derive_transcript(asset: MediaAsset, job: PipelineJob) -> Optional[dict]:
    """Derive a transcript from audio/video using the configured transcription backend."""
    existing_payload = _load_existing_transcript_payload(asset)
    if existing_payload:
        logger.info("Reusing transcript sidecar for %s", asset.filename)
        return existing_payload

    try:
        import transcription_service
        if not transcription_service.is_available():
            transcription_service.init_transcription_model()
        if not transcription_service.is_available():
            logger.info("Transcription service not available, skipping transcript derivation")
            return None

        transcription, meta, segments = transcription_service.transcribe_media_file(
            asset.path,
            filename=asset.filename,
            word_timestamps=True,
        )
        cleaned_segments, cleanup_meta = clean_transcript_segments(segments)
        transcript_meta = dict(meta or {})
        transcript_meta.update(cleanup_meta)
        transcript_meta["segment_count"] = len(cleaned_segments)
        readable_text = build_readable_transcript_text(cleaned_segments)
        if not readable_text:
            readable_text = " ".join(str(part.get("text") or "").strip() for part in cleaned_segments).strip()
        return {"text": readable_text, "meta": transcript_meta, "segments": cleaned_segments}

    except ImportError:
        logger.info("transcription_service not available")
        return None
    except Exception as e:
        logger.warning("Transcript derivation failed for %s: %s", asset.filename, e)
        return None


def _build_layer_artifacts(
    asset: MediaAsset,
    transcript_payload: Optional[dict],
    filter_results: dict,
    events: list,
    recaps: list,
    memory,
    document,
    job: PipelineJob,
) -> list[DerivedArtifact]:
    """Build a single canonical artifact bundle for every pipeline layer."""
    import json as _json

    artifacts: list[DerivedArtifact] = []

    transcript_segments = transcript_payload.get("segments", []) if transcript_payload else []
    transcript_text = transcript_payload.get("text", "") if transcript_payload else ""
    transcript_meta = transcript_payload.get("meta", {}) if transcript_payload else {}
    if transcript_text:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="transcript",
            start_s=0.0,
            end_s=asset.duration_s,
            content=transcript_text,
            confidence=transcript_meta.get("lang_p", 1.0),
            metadata={"layer": "T", **transcript_meta},
        ))

    for idx, segment in enumerate(filter_results.get("speech_segments", [])):
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="speech_segment",
            start_s=segment.start_s,
            end_s=segment.end_s,
            content=segment.text,
            confidence=segment.confidence,
            metadata={
                "layer": "L1",
                "speaker": segment.speaker,
                "salience_tags": [
                    tag.value if hasattr(tag, "value") else str(tag)
                    for tag in segment.salience_tags
                ],
                "word_timestamps": segment.word_timestamps,
                "segment_index": idx,
                "transcript_segment_count": len(transcript_segments),
            },
            source_refs=[f"speech_{segment.start_s:.2f}"],
        ))

    # ── L1: Scene segments ──────────────────────────────────────────
    for scene in filter_results.get("scenes", []):
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="scene",
            start_s=scene.start_s,
            end_s=scene.end_s,
            content=_json.dumps({
                "scene_score": scene.scene_score,
                "motion_score": scene.motion_score,
                "sharpness_score": scene.sharpness_score,
                "keyframe_path": scene.keyframe_path,
                "ocr_text": scene.ocr_text,
                "labels": scene.labels,
            }),
            confidence=min(1.0, scene.scene_score / 0.5) if scene.scene_score > 0 else 0.5,
            metadata={"layer": "L1"},
        ))

    for idx, keyframe_path in enumerate(filter_results.get("keyframes", [])):
        keyframe_start = float(idx)
        keyframe_end = float(idx)
        if idx < len(filter_results.get("scenes", [])):
            keyframe_start = filter_results["scenes"][idx].start_s
            keyframe_end = filter_results["scenes"][idx].end_s
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="keyframe",
            start_s=keyframe_start,
            end_s=keyframe_end,
            content="",
            confidence=1.0,
            metadata={"layer": "L1", "path": keyframe_path, "index": idx},
            source_refs=[f"keyframe:{keyframe_path}"],
        ))

    # ── L2: Atomic events ───────────────────────────────────────────
    for evt in events:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="event",
            start_s=evt.time_start,
            end_s=evt.time_end,
            content=evt.text_evidence,
            confidence=evt.confidence,
            metadata={
                "layer": "L2",
                "event_id": evt.event_id,
                "event_type": evt.event_type.value if hasattr(evt.event_type, 'value') else str(evt.event_type),
                "speakers": evt.speakers,
                "visual_entities": evt.visual_entities,
                "salience_tags": [t.value if hasattr(t, 'value') else str(t) for t in evt.salience_tags],
                **evt.metadata,
            },
            source_refs=evt.source_refs,
        ))

    # ── L3: Recaps ──────────────────────────────────────────────────
    for recap in recaps:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="recap",
            start_s=recap.time_start,
            end_s=recap.time_end,
            content=recap.recap_text,
            confidence=1.0,
            metadata={
                "layer": "L3",
                "recap_id": recap.recap_id,
                "group_type": recap.group_type,
                "window_summary": recap.window_summary,
                "salient_entities": recap.salient_entities,
                "unresolved_questions": recap.unresolved_questions,
                "emotional_tone": recap.emotional_tone,
                "causal_links": recap.causal_links,
                "event_ids": recap.event_ids,
                "summary_refs": recap.summary_refs,
                "ledger_entries": recap.ledger_entries,
            },
            source_refs=recap.source_refs,
        ))

    # ── L4: Contextual memory ───────────────────────────────────────
    artifacts.append(DerivedArtifact(
        media_id=asset.media_id,
        kind="memory",
        start_s=0.0,
        end_s=asset.duration_s,
        content=_json.dumps({
            "memory_id": memory.memory_id,
            "context_overview": memory.context_overview,
            "main_actors": memory.main_actors,
            "timeline_anchors": memory.timeline_anchors,
            "locations": memory.locations,
            "open_loops": memory.open_loops,
            "inferred_themes": memory.inferred_themes,
            "risk_safety_issues": memory.risk_safety_issues,
            "contradictions": memory.contradictions,
            "notable_evidence": memory.notable_evidence,
            "final_takeaways": memory.final_takeaways,
            "interpretive_notes": memory.interpretive_notes,
            "evidence_map": memory.evidence_map,
            "recap_ids": memory.recap_ids,
        }),
        confidence=1.0,
        metadata={"layer": "L4", "memory_id": memory.memory_id},
    ))

    # ── L5: Composed document ───────────────────────────────────────
    artifacts.append(DerivedArtifact(
        media_id=asset.media_id,
        kind="document",
        start_s=0.0,
        end_s=asset.duration_s,
        content=document.full_text,
        confidence=1.0,
        metadata={
            "layer": "L5",
            "document_id": document.document_id,
            "format": document.format.value if hasattr(document.format, 'value') else str(document.format),
            "title": document.title,
            "section_count": len(document.sections),
            "memory_id": document.memory_id,
        },
        source_refs=document.source_refs,
    ))

    artifacts.sort(key=lambda artifact: (artifact.start_s, artifact.end_s, artifact.kind, artifact.artifact_id))

    logger.info(
        "Saved %d trace artifacts for %s (scenes=%d, events=%d, recaps=%d, memory=1, doc=1)",
        len(artifacts), asset.filename,
        len(filter_results.get("scenes", [])), len(events), len(recaps),
    )
    return artifacts


def _format_vtt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def _parse_vtt_timestamp_seconds(value: str) -> float:
    raw = str(value or "").strip().replace(",", ".")
    parts = raw.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid VTT timestamp: {value}")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return max(0.0, hours * 3600 + minutes * 60 + seconds)


def _write_transcript_sidecar(
    asset: MediaAsset,
    transcript_payload: Optional[dict],
    pipeline_stamp: Optional[dict[str, object]] = None,
) -> Optional[Path]:
    vtt_text = _build_transcript_vtt_text(asset, transcript_payload, pipeline_stamp=pipeline_stamp)
    if not vtt_text:
        return None

    vtt_path = _sidecar_path_for_write(asset.path, ".vtt")
    vtt_path.write_text(vtt_text, encoding="utf-8")
    return vtt_path


def _build_transcript_vtt_text(
    asset: MediaAsset,
    transcript_payload: Optional[dict],
    pipeline_stamp: Optional[dict[str, object]] = None,
) -> Optional[str]:
    if not transcript_payload:
        return None
    segments = transcript_payload.get("segments") or []
    if not segments:
        return None

    meta = transcript_payload.get("meta", {})
    lines = [
        "WEBVTT",
        "",
        "NOTE",
        f"Source: {asset.path}",
        f"Language: {meta.get('lang', 'en')}",
        (
            f"Archivist-Pipeline: {pipeline_stamp.get('pipeline_version')}"
            if isinstance(pipeline_stamp, dict) and pipeline_stamp.get("pipeline_version")
            else None
        ),
        (
            f"Archivist-Commit: {pipeline_stamp.get('repo_commit')}"
            if isinstance(pipeline_stamp, dict) and pipeline_stamp.get("repo_commit")
            else None
        ),
        (
            f"Archivist-Compat: {pipeline_stamp.get('pipeline_compat_version')}"
            if isinstance(pipeline_stamp, dict) and pipeline_stamp.get("pipeline_compat_version")
            else None
        ),
        (
            f"Archivist-Stamp: {_embedded_processing_stamp_text(pipeline_stamp)}"
            if isinstance(pipeline_stamp, dict)
            else None
        ),
        "",
    ]
    lines = [line for line in lines if line is not None]
    for segment in segments:
        if isinstance(segment, dict):
            start_s = float(segment.get("start", 0.0) or 0.0)
            end_s = float(segment.get("end", start_s) or start_s)
            text = (segment.get("text") or "").strip()
        else:
            start_s = float(getattr(segment, "start", 0.0) or 0.0)
            end_s = float(getattr(segment, "end", start_s) or start_s)
            text = str(getattr(segment, "text", "") or "").strip()
        if not text:
            continue
        lines.extend([
            f"{_format_vtt_timestamp(start_s)} --> {_format_vtt_timestamp(end_s)}",
            text,
            "",
        ])
    if len(lines) <= 6:
        return None
    return "\n".join(lines)


def _existing_transcript_sidecar(asset: MediaAsset) -> Optional[Path]:
    return _existing_sidecar_path(asset.path, ".vtt")


def _load_existing_transcript_payload(asset: MediaAsset) -> Optional[dict]:
    vtt_path = _existing_transcript_sidecar(asset)
    if vtt_path is None:
        return None

    try:
        raw = vtt_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError as exc:
        logger.warning("Failed to read transcript sidecar for %s: %s", asset.filename, exc)
        return None

    segments: list[dict] = []
    transcript_lines: list[str] = []
    language = "en"
    lines = raw.split("\n")
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("NOTE"):
            index += 1
            while index < len(lines) and lines[index].strip():
                note_line = lines[index].strip()
                if note_line.lower().startswith("language:"):
                    language = note_line.split(":", 1)[1].strip() or language
                index += 1
            continue
        if "-->" not in line:
            index += 1
            continue

        try:
            start_raw, end_raw = [part.strip() for part in line.split("-->", 1)]
            start_s = _parse_vtt_timestamp_seconds(start_raw.split()[0])
            end_s = _parse_vtt_timestamp_seconds(end_raw.split()[0])
        except (ValueError, IndexError):
            index += 1
            continue

        index += 1
        cue_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            cue_lines.append(lines[index].strip())
            index += 1

        text = " ".join(cue_lines).strip()
        if not text or end_s <= start_s:
            continue

        transcript_lines.append(text)
        segments.append({
            "start": start_s,
            "end": end_s,
            "text": text,
            "no_speech_prob": 0.0,
        })

    if not segments:
        return None

    cleaned_segments, cleanup_meta = clean_transcript_segments(segments)
    readable_text = build_readable_transcript_text(cleaned_segments)

    return {
        "text": readable_text,
        "meta": {
            "lang": language,
            "source": "transcript_sidecar",
            "reused": True,
            "segment_count": len(cleaned_segments),
            **cleanup_meta,
        },
        "segments": cleaned_segments,
    }


def _count_ffprobe_streams(path: Path, stream_selector: str) -> int:
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", stream_selector,
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return 0
        payload = json.loads(result.stdout or "{}")
        return len(payload.get("streams", []))
    except Exception:
        return 0


def _probe_streams(path: Path) -> list[dict]:
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        payload = json.loads(result.stdout or "{}")
        return payload.get("streams", [])
    except Exception:
        return []


def _find_archivist_embedded_streams(path: Path) -> tuple[list[int], list[int]]:
    subtitle_indexes: list[int] = []
    attachment_indexes: list[int] = []

    for stream in _probe_streams(path):
        try:
            stream_index = int(stream.get("index"))
        except (TypeError, ValueError):
            continue
        tags = stream.get("tags") or {}
        codec_type = stream.get("codec_type")
        if codec_type == "subtitle" and tags.get("title") == "Archivist Transcript":
            subtitle_indexes.append(stream_index)
        if codec_type == "attachment" and tags.get("filename") == "archivist_media_pipeline.json":
            attachment_indexes.append(stream_index)

    return subtitle_indexes, attachment_indexes


def _inject_metadata_into_file(
    asset: MediaAsset,
    memory,
    document,
    transcript_payload: Optional[dict] = None,
    result_path: Optional[Path] = None,
    subject_line: Optional[str] = None,
    pipeline_stamp: Optional[dict[str, object]] = None,
) -> dict:
    """Inject transcript, artifact bundle, and summary metadata back into the source file."""
    import subprocess

    info = {
        "status": "skipped",
        "transcript_sidecar_path": None,
        "transcript_stream_embedded": False,
        "artifact_bundle_attached": False,
        "summary_tags_written": False,
        "error": None,
    }

    if asset.modality not in (Modality.AUDIO, Modality.VIDEO):
        return info

    src = Path(asset.path)
    if not src.exists():
        info["error"] = f"source file missing: {src}"
        logger.warning("Cannot inject metadata - %s", info["error"])
        return info

    transcript_sidecar = _write_transcript_sidecar(asset, transcript_payload, pipeline_stamp=pipeline_stamp)
    if transcript_sidecar is None:
        transcript_sidecar = _existing_transcript_sidecar(asset)
    if transcript_sidecar:
        info["transcript_sidecar_path"] = str(transcript_sidecar)

    metadata_args = []
    title_text = str(subject_line or (document.title if document else "") or "").strip()
    if title_text:
        metadata_args.extend(["-metadata", f"title={title_text}"])
    if document and document.title and document.title != title_text:
        metadata_args.extend(["-metadata", f"description={document.title}"])

    description_parts = []
    if memory.inferred_themes:
        description_parts.append(f"Themes: {', '.join(memory.inferred_themes)}")
    cleaned_participants = _clean_subject_participants(memory.main_actors, limit=8)
    if cleaned_participants:
        description_parts.append(f"Participants: {', '.join(cleaned_participants)}")
    if memory.open_loops:
        description_parts.append(f"Open questions: {len(memory.open_loops)}")
    if result_path:
        description_parts.append(f"Archivist bundle: {result_path.name}")
    if pipeline_stamp:
        description_parts.append(_embedded_processing_stamp_text(pipeline_stamp))
    if description_parts:
        metadata_args.extend(["-metadata", f"comment={' | '.join(description_parts)}"])

    if cleaned_participants:
        metadata_args.extend(["-metadata", f"artist={', '.join(cleaned_participants[:5])}"])

    if document and document.format:
        fmt_label = document.format.value if hasattr(document.format, "value") else str(document.format)
        metadata_args.extend(["-metadata", f"genre={fmt_label}"])
    if pipeline_stamp:
        hash_preview = str(pipeline_stamp.get("source_file_hash") or "").strip()[:12]
        version_tag = str(
            pipeline_stamp.get("repo_commit_suffix")
            or pipeline_stamp.get("pipeline_version")
            or MEDIA_PIPELINE_VERSION
        ).strip()
        compat_version = str(
            pipeline_stamp.get("pipeline_compat_version")
            or MEDIA_PIPELINE_COMPAT_VERSION
        ).strip()
        metadata_args.extend([
            "-metadata",
            (
                "keywords="
                f"archivist,media-pipeline,version:{version_tag or 'unknown'},"
                f"compat:{compat_version or 'unknown'},hash:{hash_preview or 'unknown'}"
            ),
        ])

    suffix = src.suffix.lower()
    embed_transcript_stream = transcript_sidecar is not None and suffix in {".mkv", ".mp4"}
    attach_artifact_bundle = result_path is not None and suffix == ".mkv"

    if not metadata_args and not embed_transcript_stream and not attach_artifact_bundle:
        return info

    tmp_path = src.with_name(f"{src.stem}.archivist_tmp{src.suffix}")
    try:
        cmd = [
            *LOWPRI_PREFIX, "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
        ]
        existing_archivist_subtitles, existing_archivist_attachments = _find_archivist_embedded_streams(src)
        subtitle_stream_index = None
        if embed_transcript_stream and transcript_sidecar is not None:
            subtitle_stream_index = max(
                0,
                _count_ffprobe_streams(src, "s") - len(existing_archivist_subtitles),
            )
            cmd.extend(["-i", str(transcript_sidecar)])

        cmd.extend(["-map", "0"])
        if embed_transcript_stream:
            for stream_index in existing_archivist_subtitles:
                cmd.extend(["-map", f"-0:{stream_index}"])
        if attach_artifact_bundle:
            for stream_index in existing_archivist_attachments:
                cmd.extend(["-map", f"-0:{stream_index}"])
        if embed_transcript_stream:
            cmd.extend(["-map", "1:0"])

        if suffix == ".mp4":
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])
            if embed_transcript_stream:
                cmd.extend(["-c:s", "mov_text"])
            else:
                cmd.extend(["-c", "copy"])
        else:
            cmd.extend(["-c", "copy"])

        cmd.extend(["-map_metadata", "0"])
        cmd.extend(metadata_args)

        if embed_transcript_stream and subtitle_stream_index is not None:
            cmd.extend([
                f"-metadata:s:s:{subtitle_stream_index}", "language=eng",
                f"-metadata:s:s:{subtitle_stream_index}", "title=Archivist Transcript",
            ])

        if attach_artifact_bundle and result_path is not None:
            attachment_index = max(
                0,
                _count_ffprobe_streams(src, "t") - len(existing_archivist_attachments),
            )
            cmd.extend([
                "-attach", str(result_path),
                f"-metadata:s:t:{attachment_index}", "mimetype=application/json",
                f"-metadata:s:t:{attachment_index}", "filename=archivist_media_pipeline.json",
            ])

        cmd.append(str(tmp_path))
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=max(300, int(src.stat().st_size / (8 * 1024 * 1024))),
        )
        if result.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 0:
            tmp_path.replace(src)
            info["status"] = "embedded"
            info["summary_tags_written"] = bool(metadata_args)
            info["transcript_stream_embedded"] = embed_transcript_stream
            info["artifact_bundle_attached"] = attach_artifact_bundle
            logger.info("Injected metadata into %s", asset.filename)
            return info

        stderr = (result.stderr or b"").decode("utf-8", errors="ignore")
        info["status"] = "error"
        info["error"] = stderr[:500]
        logger.warning("Metadata injection failed for %s: %s", asset.filename, stderr[:200])
    except Exception as e:
        info["status"] = "error"
        info["error"] = str(e)
        logger.warning("Metadata injection error for %s: %s", asset.filename, e)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return info


def _trace_artifacts_to_vectorstore_chunks(
    asset: MediaAsset,
    trace_artifacts: list[DerivedArtifact],
):
    from hashlib import sha256
    from transcripts.chunking import TranscriptChunk

    source_id = _expected_vectorstore_source_id(asset.media_id)
    display_path = asset.path
    chunks: list[TranscriptChunk] = []

    for artifact in trace_artifacts:
        text = str(artifact.content or "").strip()
        if artifact.kind == "speech_segment":
            if len(text.split()) < 3:
                continue
            chunk_seed = (
                f"{source_id}|0|{int(artifact.start_s * 1000)}|"
                f"{int((artifact.end_s - artifact.start_s))}|{text[:100]}"
            )
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    path=display_path,
                    text=text,
                    t_start_ms=int(artifact.start_s * 1000),
                    t_end_ms=int(artifact.end_s * 1000),
                    chunk_duration_s=max(1, int(artifact.end_s - artifact.start_s)),
                    level=0,
                    parent_id=None,
                    doc_type="media_transcript",
                    source_type="media",
                    topic_label=None,
                    language=None,
                    tag="utterance",
                )
            )
            continue

        if artifact.kind == "event":
            if len(text.split()) < 5:
                continue
            event_type = str(artifact.metadata.get("event_type") or "event").strip() or "event"
            speakers = artifact.metadata.get("speakers") or []
            context_prefix = f"[{', '.join(str(s) for s in speakers)}] " if speakers else ""
            chunk_seed = (
                f"{source_id}|1|{int(artifact.start_s * 1000)}|"
                f"{int(artifact.end_s - artifact.start_s)}|event"
            )
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    path=display_path,
                    text=f"{context_prefix}{text}",
                    t_start_ms=int(artifact.start_s * 1000),
                    t_end_ms=int(artifact.end_s * 1000),
                    chunk_duration_s=max(1, int(artifact.end_s - artifact.start_s)),
                    level=1,
                    parent_id=None,
                    doc_type="media_event",
                    source_type="media",
                    topic_label=event_type,
                    language=None,
                    tag=f"event_{event_type}",
                )
            )
            continue

        if artifact.kind == "recap":
            if len(text.split()) < 8:
                continue
            chunk_seed = f"{source_id}|2|{int(artifact.start_s * 1000)}|60|recap"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    path=display_path,
                    text=text,
                    t_start_ms=int(artifact.start_s * 1000),
                    t_end_ms=int(artifact.end_s * 1000),
                    chunk_duration_s=max(1, int(artifact.end_s - artifact.start_s)),
                    level=2,
                    parent_id=None,
                    doc_type="media_recap",
                    source_type="media",
                    topic_label=str(artifact.metadata.get("group_type") or "").strip() or None,
                    language=None,
                    tag="recap",
                )
            )
            continue

        if artifact.kind == "document":
            if len(text.split()) < 10:
                continue
            chunk_seed = f"{source_id}|3|0|{int(asset.duration_s)}|doc"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    path=display_path,
                    text=text[:65000],
                    t_start_ms=0,
                    t_end_ms=int(asset.duration_s * 1000),
                    chunk_duration_s=max(1, int(asset.duration_s)),
                    level=3,
                    parent_id=None,
                    doc_type="media_document",
                    source_type="media",
                    topic_label=str(artifact.metadata.get("format") or "").strip() or None,
                    language=None,
                    tag="doc_chunk",
                )
            )

    return chunks


def _insert_vectorstore_chunks(asset: MediaAsset, chunks) -> dict:
    stats = {
        "chunks_created": len(chunks),
        "chunks_inserted": 0,
        "collection": "documents_transcripts",
        "error": None,
        "source_id": _expected_vectorstore_source_id(asset.media_id),
        "file_hash": asset.file_hash or "",
    }
    if not chunks:
        stats["error"] = "No chunks generated from pipeline output"
        return stats

    alias = f"media_{asset.media_id[:8]}"
    collection = None
    try:
        import os
        from indexing_service import (
            _ensure_chunk_collection,
            _insert_chunks,
            TRANSCRIPT_COLLECTION,
        )
        from pymilvus import connections

        embedding_host = os.getenv("EMBEDDING_HOST", "localhost")
        embedding_port = int(os.getenv("EMBEDDING_PORT", "8000"))
        collection = _ensure_chunk_collection(
            TRANSCRIPT_COLLECTION,
            description="Documents and transcripts",
            alias=alias,
            ip_address=os.getenv("MILVUS_HOST", "localhost"),
        )
        try:
            collection.load()
        except Exception:
            pass

        try:
            delete_expr = f'source_id == "{_expected_vectorstore_source_id(asset.media_id)}"'
            collection.delete(delete_expr)
            collection.flush()
        except Exception:
            pass

        inserted = _insert_chunks(
            collection=collection,
            chunks=chunks,
            filehash=asset.file_hash or "",
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        try:
            collection.flush()
        except Exception:
            pass
        stats["chunks_inserted"] = inserted
        stats["collection"] = TRANSCRIPT_COLLECTION
        logger.info(
            "Vectorstore: inserted %d/%d chunks for %s into %s",
            inserted, len(chunks), asset.filename, TRANSCRIPT_COLLECTION,
        )
    except Exception as exc:
        stats["error"] = str(exc)
        logger.warning("Vectorstore insertion failed for %s: %s", asset.media_id, exc)
    finally:
        if collection is not None:
            try:
                collection.release()
            except Exception:
                pass
        try:
            from pymilvus import connections

            connections.disconnect(alias)
        except Exception:
            pass
    return stats


def _insert_trace_artifacts_into_vectorstore(asset: MediaAsset, trace_artifacts: list[DerivedArtifact]) -> dict:
    return _insert_vectorstore_chunks(
        asset,
        _trace_artifacts_to_vectorstore_chunks(asset, trace_artifacts),
    )


def _backfill_saved_vectorstore_projection(asset: MediaAsset, result: Optional[dict]) -> dict:
    if not isinstance(result, dict):
        return {
            "chunks_created": 0,
            "chunks_inserted": 0,
            "collection": "documents_transcripts",
            "error": "Saved pipeline result missing",
            "source_id": _expected_vectorstore_source_id(asset.media_id),
            "file_hash": asset.file_hash or "",
        }

    trace_artifacts = get_artifacts(asset.media_id, scope="trace")
    if not trace_artifacts:
        return {
            "chunks_created": 0,
            "chunks_inserted": 0,
            "collection": "documents_transcripts",
            "error": "No trace artifacts available for vectorstore backfill",
            "source_id": _expected_vectorstore_source_id(asset.media_id),
            "file_hash": asset.file_hash or "",
        }

    stats = _insert_trace_artifacts_into_vectorstore(asset, trace_artifacts)
    layers = dict(result.get("layers") or {})
    layers["L6_vectorstore"] = stats
    result["layers"] = layers
    _save_pipeline_result(asset.media_id, result)
    return stats


def backfill_saved_media_vectorstore(media_ids: Optional[list[str]] = None, limit: Optional[int] = None) -> dict:
    requested_ids = [str(media_id or "").strip() for media_id in (media_ids or []) if str(media_id or "").strip()]
    candidates: list[MediaAsset] = []
    if requested_ids:
        for media_id in requested_ids:
            asset = get_asset(media_id)
            if asset is not None:
                candidates.append(asset)
    else:
        for item in list_assets():
            media_id = str(item.get("media_id") or "").strip()
            if not media_id:
                continue
            asset = get_asset(media_id)
            if asset is not None:
                candidates.append(asset)

    summary = {
        "checked": 0,
        "backfilled": 0,
        "skipped_current": 0,
        "failed": 0,
        "results": [],
    }

    for asset in candidates:
        if limit is not None and summary["checked"] >= max(0, int(limit)):
            break
        summary["checked"] += 1
        if _media_job_active(asset.media_id):
            summary["results"].append({
                "media_id": asset.media_id,
                "path": asset.path,
                "status": "skipped_active_job",
            })
            continue
        saved_result = _load_saved_pipeline_result(asset.media_id)
        if not _pipeline_result_is_current(
            saved_result,
            asset_path=asset.path,
            asset_file_hash=asset.file_hash,
            asset_file_size_bytes=asset.file_size_bytes,
        ):
            summary["results"].append({
                "media_id": asset.media_id,
                "path": asset.path,
                "status": "skipped_pipeline_stale",
            })
            continue

        if _vectorstore_layer_is_current(
            saved_result,
            media_id=asset.media_id,
            asset_file_hash=asset.file_hash,
        ):
            summary["skipped_current"] += 1
            summary["results"].append({
                "media_id": asset.media_id,
                "path": asset.path,
                "status": "already_current",
            })
            continue

        stats = _backfill_saved_vectorstore_projection(asset, saved_result)
        if stats.get("error"):
            summary["failed"] += 1
            status = "error"
        else:
            summary["backfilled"] += 1
            status = "backfilled"
        summary["results"].append({
            "media_id": asset.media_id,
            "path": asset.path,
            "status": status,
            "vectorstore": stats,
        })

    return summary


def _insert_into_vectorstore(
    asset: MediaAsset,
    filter_results: dict,
    events: list,
    recaps: list,
    memory,
    document,
) -> dict:
    """L6: Insert processed media into Milvus vectorstore.

    Converts the pipeline output into TranscriptChunk objects that slot
    into the existing indexing infrastructure. Uses the same collection
    schema (documents_transcripts) so media transcripts are searchable
    alongside manually-indexed transcript files.

    Creates chunks at multiple levels per the QA retrieval research:
    - Utterance-level (speech segments) for fine-grained answer retrieval
    - Event-level (atomic events) for contextual search
    - Recap-level (60s windows) for broader topic search
    - Document-level (full composed output) for high-level queries

    The hybrid retrieval (dense + BM25 sparse) in the existing search
    infrastructure handles both semantic and keyword matching automatically.
    """
    stats = {
        "chunks_created": 0,
        "chunks_inserted": 0,
        "collection": "",
        "error": None,
        "source_id": _expected_vectorstore_source_id(asset.media_id),
        "file_hash": asset.file_hash or "",
    }
    alias = f"media_{asset.media_id[:8]}"
    collection = None

    try:
        from transcripts.chunking import TranscriptChunk
        from hashlib import sha256
        import os

        speech_segments = filter_results.get("speech_segments", [])
        if not speech_segments and not events:
            stats["error"] = "No speech segments or events to index"
            return stats

        source_id = f"media:{asset.media_id}"
        display_path = asset.path
        filehash = asset.file_hash or ""

        chunks: list[TranscriptChunk] = []

        # ── Utterance-level chunks (from speech segments) ───────────
        # These are the fine-grained chunks for answer retrieval.
        # Per QA research: short answer-bearing passages rank better
        # when they're stored as their own chunks rather than buried
        # in large windows.
        for seg in speech_segments:
            text = seg.text.strip()
            if not text or len(text.split()) < 3:
                continue
            chunk_seed = f"{source_id}|0|{int(seg.start_s * 1000)}|{int((seg.end_s - seg.start_s))}|{text[:100]}"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=text,
                t_start_ms=int(seg.start_s * 1000),
                t_end_ms=int(seg.end_s * 1000),
                chunk_duration_s=max(1, int(seg.end_s - seg.start_s)),
                level=0,
                parent_id=None,
                doc_type="media_transcript",
                source_type="media",
                topic_label=None,
                language=None,
                tag="utterance",
            ))

        # ── Event-level chunks (merged speech windows) ──────────────
        # Per QA research: contextual chunk embeddings improve retrieval.
        # Events carry more context than raw utterances.
        for evt in events:
            text = evt.text_evidence.strip()
            if not text or len(text.split()) < 5:
                continue
            chunk_seed = f"{source_id}|1|{int(evt.time_start * 1000)}|{int(evt.time_end - evt.time_start)}|event"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            # Add speaker context to improve retrieval
            context_prefix = ""
            if evt.speakers:
                context_prefix = f"[{', '.join(evt.speakers)}] "
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=f"{context_prefix}{text}",
                t_start_ms=int(evt.time_start * 1000),
                t_end_ms=int(evt.time_end * 1000),
                chunk_duration_s=max(1, int(evt.time_end - evt.time_start)),
                level=1,
                parent_id=None,
                doc_type="media_event",
                source_type="media",
                topic_label=evt.event_type.value if hasattr(evt.event_type, 'value') else str(evt.event_type),
                language=None,
                tag=f"event_{evt.event_type.value}" if hasattr(evt.event_type, 'value') else "event",
            ))

        # ── Recap-level chunks (60s window summaries) ───────────────
        # These provide topic-level search coverage.
        for recap in recaps:
            text = recap.recap_text.strip()
            if not text or len(text.split()) < 8:
                continue
            chunk_seed = f"{source_id}|2|{int(recap.time_start * 1000)}|60|recap"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=text,
                t_start_ms=int(recap.time_start * 1000),
                t_end_ms=int(recap.time_end * 1000),
                chunk_duration_s=max(1, int(recap.time_end - recap.time_start)),
                level=2,
                parent_id=None,
                doc_type="media_recap",
                source_type="media",
                topic_label=recap.group_type,
                language=None,
                tag="recap",
            ))

        # ── Document-level chunk (composed output) ──────────────────
        # This gives the high-level summary for broad queries.
        if document and document.full_text and len(document.full_text.split()) >= 10:
            chunk_seed = f"{source_id}|3|0|{int(asset.duration_s)}|doc"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=document.full_text[:65000],
                t_start_ms=0,
                t_end_ms=int(asset.duration_s * 1000),
                chunk_duration_s=max(1, int(asset.duration_s)),
                level=3,
                parent_id=None,
                doc_type="media_document",
                source_type="media",
                topic_label=document.format.value if hasattr(document.format, 'value') else str(document.format),
                language=None,
                tag="doc_chunk",
            ))

        stats["chunks_created"] = len(chunks)

        if not chunks:
            stats["error"] = "No chunks generated from pipeline output"
            return stats

        # ── Insert into Milvus via existing indexing infrastructure ──
        from indexing_service import (
            _ensure_chunk_collection,
            _insert_chunks,
            TRANSCRIPT_COLLECTION,
        )

        embedding_host = os.getenv("EMBEDDING_HOST", "localhost")
        embedding_port = int(os.getenv("EMBEDDING_PORT", "8000"))

        collection = _ensure_chunk_collection(
            TRANSCRIPT_COLLECTION,
            description="Documents and transcripts",
            alias=alias,
            ip_address=os.getenv("MILVUS_HOST", "localhost"),
        )
        try:
            collection.load()
        except Exception:
            pass

        # Delete any previous chunks for this media asset
        try:
            delete_expr = f'source_id == "media:{asset.media_id}"'
            collection.delete(delete_expr)
            collection.flush()
        except Exception:
            pass

        inserted = _insert_chunks(
            collection=collection,
            chunks=chunks,
            filehash=filehash,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        try:
            collection.flush()
        except Exception:
            pass
        stats["chunks_inserted"] = inserted
        stats["collection"] = TRANSCRIPT_COLLECTION

        logger.info(
            "Vectorstore: inserted %d/%d chunks for %s into %s",
            inserted, len(chunks), asset.filename, TRANSCRIPT_COLLECTION,
        )

    except Exception as e:
        stats["error"] = str(e)
        logger.warning("Vectorstore insertion failed for %s: %s", asset.media_id, e)
    finally:
        if collection is not None:
            try:
                collection.release()
            except Exception:
                pass
        try:
            from pymilvus import connections

            connections.disconnect(alias)
        except Exception:
            pass

    return stats


def _save_pipeline_result(media_id: str, result: dict):
    """Persist pipeline results to disk."""
    PIPELINE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    result_file = PIPELINE_STORE_DIR / f"{media_id}.json"
    # Convert non-serializable objects
    serializable = json.loads(json.dumps(result, default=str))
    result_file.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return result_file


# ---------------------------------------------------------------------------
# Compat-version migration and status
# ---------------------------------------------------------------------------

_pipeline_compat_cache: dict = {}
_pipeline_compat_cache_ts: float = 0.0
_pipeline_compat_cache_dir: str = ""
_PIPELINE_COMPAT_CACHE_TTL = 300.0  # 5 minutes — this changes slowly


def pipeline_compat_status() -> dict:
    """Return counts of current, stale, and broken pipeline results (cached 5min)."""
    import time as _time
    global _pipeline_compat_cache, _pipeline_compat_cache_ts, _pipeline_compat_cache_dir
    store_dir = str(PIPELINE_STORE_DIR)
    if (
        _pipeline_compat_cache
        and _pipeline_compat_cache_dir == store_dir
        and (_time.time() - _pipeline_compat_cache_ts) < _PIPELINE_COMPAT_CACHE_TTL
    ):
        return _pipeline_compat_cache.copy()
    current = stale = broken = ignored = 0
    if not PIPELINE_STORE_DIR.is_dir():
        return {"current": 0, "stale": 0, "broken": 0, "ignored": 0, "total": 0, "compat_version": MEDIA_PIPELINE_COMPAT_VERSION}
    for result_file in PIPELINE_STORE_DIR.glob("*.json"):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            broken += 1
            continue
        if not _looks_like_pipeline_result(data):
            ignored += 1
            continue
        stamp = data.get("archivist_pipeline")
        if not isinstance(stamp, dict):
            if _result_has_pipeline_output(data):
                stale += 1
            else:
                broken += 1
            continue
        stamped_cv = str(stamp.get("pipeline_compat_version") or "").strip()
        if stamped_cv == MEDIA_PIPELINE_COMPAT_VERSION:
            current += 1
        elif data.get("document") or data.get("transcript"):
            stale += 1
        else:
            broken += 1
    result = {
        "current": current,
        "stale": stale,
        "broken": broken,
        "ignored": ignored,
        "total": current + stale + broken,
        "compat_version": MEDIA_PIPELINE_COMPAT_VERSION,
    }
    _pipeline_compat_cache.clear()
    _pipeline_compat_cache.update(result)
    _pipeline_compat_cache_ts = _time.time()
    _pipeline_compat_cache_dir = store_dir
    return result


def migrate_pipeline_compat_version(*, dry_run: bool = False, verify_sources: bool = False) -> dict:
    """Stamp existing valid pipeline results with the current compat version.

    Only updates results that have valid data (document or transcript).
    Source mtime verification is optional because network/media mounts can
    block the health endpoint; per-asset freshness still runs before reuse.
    """
    migrated = 0
    skipped_invalid = 0
    skipped_changed = 0
    skipped_current = 0
    ignored = 0
    errors = 0

    if not PIPELINE_STORE_DIR.is_dir():
        return {
            "migrated": 0,
            "skipped_invalid": 0,
            "skipped_changed": 0,
            "skipped_current": 0,
            "ignored": 0,
            "errors": 0,
            "dry_run": dry_run,
            "verify_sources": verify_sources,
        }

    for result_file in PIPELINE_STORE_DIR.glob("*.json"):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            errors += 1
            continue

        if not _looks_like_pipeline_result(data):
            ignored += 1
            continue

        stamp = data.get("archivist_pipeline")
        created_legacy_stamp = False
        if not isinstance(stamp, dict):
            if not _result_has_pipeline_output(data):
                skipped_invalid += 1
                continue
            stamp = _legacy_pipeline_stamp_from_result(data, result_file)
            data["archivist_pipeline"] = stamp
            created_legacy_stamp = True

        # Already current
        stamped_cv = str(stamp.get("pipeline_compat_version") or "").strip()
        if stamped_cv == MEDIA_PIPELINE_COMPAT_VERSION and not created_legacy_stamp:
            skipped_current += 1
            continue

        # Must have produced real output
        if not _result_has_pipeline_output(data):
            skipped_invalid += 1
            continue

        # Verify source file still matches
        source_path = str(stamp.get("source_path") or "").strip()
        if verify_sources and source_path:
            current_mtime = _current_source_mtime_ns(source_path)
            stamped_mtime = stamp.get("source_mtime_ns")
            if current_mtime is None:
                # Source file gone -- skip, needs reprocess
                skipped_changed += 1
                continue
            if stamped_mtime is not None and int(stamped_mtime) != current_mtime:
                skipped_changed += 1
                continue

        if not dry_run:
            stamp["pipeline_compat_version"] = MEDIA_PIPELINE_COMPAT_VERSION
            if isinstance(data.get("document"), dict):
                data["document"]["archivist_pipeline"] = stamp
            try:
                result_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except OSError:
                errors += 1
                continue
        migrated += 1

    return {
        "migrated": migrated,
        "skipped_invalid": skipped_invalid,
        "skipped_changed": skipped_changed,
        "skipped_current": skipped_current,
        "ignored": ignored,
        "errors": errors,
        "dry_run": dry_run,
        "verify_sources": verify_sources,
        "compat_version": MEDIA_PIPELINE_COMPAT_VERSION,
    }


def get_pipeline_result(media_id: str) -> Optional[dict]:
    """Load a stored pipeline result."""
    result_file = PIPELINE_STORE_DIR / f"{media_id}.json"
    if not result_file.exists():
        return None
    try:
        result = json.loads(result_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    transcript = result.get("transcript")
    if not isinstance(transcript, dict):
        return result

    asset_path = ""
    asset_info = result.get("asset")
    if isinstance(asset_info, dict):
        asset_path = str(asset_info.get("path") or "").strip()
    if not asset_path:
        stamp = result.get("archivist_pipeline")
        if isinstance(stamp, dict):
            asset_path = str(stamp.get("source_path") or "").strip()

    if asset_path:
        payload = _load_existing_transcript_payload(MediaAsset(path=asset_path, filename=Path(asset_path).name))
        if payload:
            transcript["text"] = payload.get("text", transcript.get("text", ""))
            transcript["meta"] = {
                **(transcript.get("meta") if isinstance(transcript.get("meta"), dict) else {}),
                **(payload.get("meta") if isinstance(payload.get("meta"), dict) else {}),
            }
            transcript["segment_count"] = len(payload.get("segments") or [])

    if isinstance(transcript.get("vtt_text"), str) and transcript.get("vtt_text", "").strip():
        return result

    injection = result.get("injection")
    if not isinstance(injection, dict):
        return result

    transcript_sidecar_path = injection.get("transcript_sidecar_path")
    if not isinstance(transcript_sidecar_path, str) or not transcript_sidecar_path.strip():
        return result

    vtt_path = Path(transcript_sidecar_path)
    if not vtt_path.exists():
        return result

    try:
        transcript["vtt_text"] = vtt_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return result
    return result
