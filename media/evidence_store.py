"""L0: Raw evidence store - register and manage media assets and derived artifacts."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Optional

from media.models import DerivedArtifact, MediaAsset, Modality, PipelineJob

logger = logging.getLogger("archivist.media.evidence")

MEDIA_STORE_DIR = Path(os.getenv("MEDIA_STORE_DIR", "/data/media_store"))
ASSETS_INDEX = MEDIA_STORE_DIR / "assets.json"
ARTIFACTS_DIR = MEDIA_STORE_DIR / "artifacts"
PIPELINE_RESULTS_DIR = Path(os.getenv("MEDIA_PIPELINE_DIR", "/data/media_pipeline"))

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".wma", ".aac", ".webm"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".ts", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"}
ALL_MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS | IMAGE_EXTS

_RECORDED_AT_FILENAME_PATTERNS = (
    re.compile(
        r"(?P<year>20\d{2})[-_](?P<month>\d{2})[-_](?P<day>\d{2})"
        r"(?:[T _-](?P<hour>\d{2})[-:](?P<minute>\d{2})(?:[-:](?P<second>\d{2}))?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})"
        r"(?:[T _-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})?)?",
        re.IGNORECASE,
    ),
)


def infer_recorded_at_from_path(path: str | Path) -> Optional[str]:
    text = str(path or "").strip()
    if not text:
        return None
    filename = Path(text).name
    for pattern in _RECORDED_AT_FILENAME_PATTERNS:
        match = pattern.search(filename)
        if not match:
            continue
        try:
            year = int(match.group("year"))
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour") or 0)
            minute = int(match.group("minute") or 0)
            second = int(match.group("second") or 0)
            return datetime(year, month, day, hour, minute, second).isoformat()
        except Exception:
            continue
    return None


def infer_recorded_day_from_path(path: str | Path) -> Optional[str]:
    recorded_at = infer_recorded_at_from_path(path)
    if not recorded_at:
        return None
    try:
        return datetime.fromisoformat(recorded_at).date().isoformat()
    except Exception:
        return recorded_at[:10] if len(recorded_at) >= 10 else None


def _compute_file_hash(path: str) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _asset_record_priority(media_id: str, data: dict) -> tuple[int, int, float, float]:
    has_pipeline = int((PIPELINE_RESULTS_DIR / f"{media_id}.json").exists())
    has_bundle = int((ARTIFACTS_DIR / f"{media_id}.json").exists() or (ARTIFACTS_DIR / media_id).exists())
    return (
        has_pipeline,
        has_bundle,
        float(data.get("indexed_at", 0.0) or 0.0),
        float(data.get("created_at", 0.0) or 0.0),
    )


def _normalize_assets_index(index: dict) -> tuple[dict, bool]:
    if not index:
        return {}, False

    normalized: dict = {}
    seen_paths: set[str] = set()
    seen_hashes: set[str] = set()
    changed = False

    sorted_items = sorted(
        index.items(),
        key=lambda item: _asset_record_priority(item[0], item[1]),
        reverse=True,
    )

    for media_id, data in sorted_items:
        path = str(data.get("path") or "")
        file_hash = str(data.get("file_hash") or "")
        if path and not Path(path).exists():
            changed = True
            continue
        if (path and path in seen_paths) or (file_hash and file_hash in seen_hashes):
            changed = True
            continue
        normalized[media_id] = data
        if path:
            seen_paths.add(path)
        if file_hash:
            seen_hashes.add(file_hash)

    return normalized, changed


def _save_assets_index(index: dict):
    MEDIA_STORE_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _detect_modality(path: str) -> Modality:
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXTS:
        return Modality.VIDEO
    if ext in AUDIO_EXTS:
        return Modality.AUDIO
    if ext in IMAGE_EXTS:
        return Modality.IMAGE
    return Modality.TEXT


def _probe_media(path: str) -> dict:
    """Use ffprobe binary to extract media metadata."""
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.warning("ffprobe failed for %s (exit %d)", path, result.returncode)
            return {}
        probe = json.loads(result.stdout)
    except FileNotFoundError:
        logger.warning("ffprobe binary not found")
        return {}
    except Exception as e:
        logger.warning("ffprobe failed for %s: %s", path, e)
        return {}

    info: dict = {}
    for stream in probe.get("streams", []):
        codec_type = stream.get("codec_type", "")
        if codec_type == "video":
            info["width"] = int(stream.get("width", 0))
            info["height"] = int(stream.get("height", 0))
            info["codec"] = stream.get("codec_name", "")
            r_frame_rate = stream.get("r_frame_rate", "0/1")
            try:
                num, den = r_frame_rate.split("/")
                info["fps"] = float(num) / float(den) if float(den) > 0 else 0.0
            except (ValueError, ZeroDivisionError):
                info["fps"] = 0.0
        elif codec_type == "audio":
            info.setdefault("codec", stream.get("codec_name", ""))
            info["sample_rate"] = int(stream.get("sample_rate", 0))

    fmt = probe.get("format", {})
    info["duration_s"] = float(fmt.get("duration", 0))
    info["file_size_bytes"] = int(fmt.get("size", 0))
    return info


def register_asset(path: str, metadata: Optional[dict] = None) -> MediaAsset:
    """Register a media file in the evidence store."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")

    resolved_path = str(file_path.resolve())
    index = _load_assets_index()
    existing_media_id = None
    existing_file_hash = ""
    try:
        existing_file_hash = _compute_file_hash(resolved_path)
    except OSError:
        existing_file_hash = ""
    for media_id, data in index.items():
        if data.get("path") == resolved_path or (
            existing_file_hash and data.get("file_hash") == existing_file_hash
        ):
            existing_media_id = media_id
            break

    modality = _detect_modality(path)
    probe_info = _probe_media(path) if modality in (Modality.AUDIO, Modality.VIDEO) else {}

    merged_metadata = dict(metadata or {})
    inferred_recorded_at = infer_recorded_at_from_path(resolved_path)
    inferred_recorded_day = infer_recorded_day_from_path(resolved_path)
    if inferred_recorded_at and not str(merged_metadata.get("recorded_at") or "").strip():
        merged_metadata["recorded_at"] = inferred_recorded_at
    if inferred_recorded_day and not str(merged_metadata.get("recorded_day") or "").strip():
        merged_metadata["recorded_day"] = inferred_recorded_day

    asset = MediaAsset(
        media_id=existing_media_id or MediaAsset().media_id,
        path=resolved_path,
        filename=file_path.name,
        modality=modality,
        file_size_bytes=probe_info.get("file_size_bytes", file_path.stat().st_size),
        duration_s=probe_info.get("duration_s", 0.0),
        sample_rate=probe_info.get("sample_rate", 0),
        width=probe_info.get("width", 0),
        height=probe_info.get("height", 0),
        fps=probe_info.get("fps", 0.0),
        codec=probe_info.get("codec", ""),
        created_at=file_path.stat().st_mtime,
        indexed_at=time.time(),
        metadata=merged_metadata,
    )
    asset.file_hash = existing_file_hash or asset.compute_hash()

    _save_asset(asset)
    logger.info("Registered media asset: %s (%s, %.1fs)", asset.filename, asset.modality, asset.duration_s)
    return asset


def _save_asset(asset: MediaAsset):
    """Persist asset metadata to the store."""
    index = _load_assets_index()
    index[asset.media_id] = {
        "media_id": asset.media_id,
        "path": asset.path,
        "filename": asset.filename,
        "modality": asset.modality.value,
        "file_hash": asset.file_hash,
        "file_size_bytes": asset.file_size_bytes,
        "duration_s": asset.duration_s,
        "sample_rate": asset.sample_rate,
        "width": asset.width,
        "height": asset.height,
        "fps": asset.fps,
        "codec": asset.codec,
        "created_at": asset.created_at,
        "indexed_at": asset.indexed_at,
        "metadata": asset.metadata,
    }
    normalized, _ = _normalize_assets_index(index)
    _save_assets_index(normalized)


def _load_assets_index() -> dict:
    if ASSETS_INDEX.exists():
        try:
            index = json.loads(ASSETS_INDEX.read_text(encoding="utf-8"))
            normalized, changed = _normalize_assets_index(index)
            if changed:
                _save_assets_index(normalized)
            return normalized
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_asset(media_id: str) -> Optional[MediaAsset]:
    """Retrieve an asset by ID."""
    index = _load_assets_index()
    data = index.get(media_id)
    if not data:
        return None
    return MediaAsset(
        media_id=data["media_id"],
        path=data["path"],
        filename=data["filename"],
        modality=Modality(data["modality"]),
        file_hash=data.get("file_hash", ""),
        file_size_bytes=data.get("file_size_bytes", 0),
        duration_s=data.get("duration_s", 0.0),
        sample_rate=data.get("sample_rate", 0),
        width=data.get("width", 0),
        height=data.get("height", 0),
        fps=data.get("fps", 0.0),
        codec=data.get("codec", ""),
        created_at=data.get("created_at", 0.0),
        indexed_at=data.get("indexed_at", 0.0),
        metadata=data.get("metadata", {}),
    )


def list_assets() -> list[dict]:
    """List all registered assets."""
    index = _load_assets_index()
    return sorted(index.values(), key=lambda a: a.get("indexed_at", 0), reverse=True)


def save_artifact(artifact: DerivedArtifact):
    """Save a derived artifact into a single per-media JSON bundle."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle_file = ARTIFACTS_DIR / f"{artifact.media_id}.json"
    bundle = {"media_id": artifact.media_id, "artifacts": []}
    if bundle_file.exists():
        try:
            bundle = json.loads(bundle_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            bundle = {"media_id": artifact.media_id, "artifacts": []}

    artifact_payload = _artifact_payload(artifact)
    artifacts = [a for a in bundle.get("artifacts", []) if a.get("artifact_id") != artifact.artifact_id]
    artifacts.append(artifact_payload)
    artifacts.sort(key=lambda a: (a.get("start_s", 0.0), a.get("end_s", 0.0), a.get("kind", "")))
    bundle["media_id"] = artifact.media_id
    bundle["artifacts"] = artifacts
    bundle_file.write_text(json.dumps(bundle, indent=2), encoding="utf-8")


def _artifact_payload(artifact: DerivedArtifact) -> dict:
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


def save_artifact_bundle(media_id: str, artifacts: list[DerivedArtifact], bundle_metadata: Optional[dict] = None):
    """Persist a full per-media artifact bundle for technical trace inspection."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle_file = ARTIFACTS_DIR / f"{media_id}.json"
    metadata = bundle_metadata or {}
    payload = {
        "media_id": media_id,
        "bundle_metadata": metadata,
        "archivist_pipeline": metadata.get("archivist_pipeline", {}),
        "artifacts": sorted(
            [_artifact_payload(artifact) for artifact in artifacts],
            key=lambda a: (a.get("start_s", 0.0), a.get("end_s", 0.0), a.get("kind", "")),
        ),
    }
    bundle_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _deserialize_artifacts(artifacts_data: list[dict], kind: Optional[str] = None) -> list[DerivedArtifact]:
    artifacts = []
    for data in artifacts_data:
        if kind and data.get("kind") != kind:
            continue
        artifacts.append(DerivedArtifact(
            artifact_id=data["artifact_id"],
            media_id=data["media_id"],
            kind=data.get("kind", ""),
            start_s=data.get("start_s", 0.0),
            end_s=data.get("end_s", 0.0),
            content=data.get("content", ""),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            source_refs=data.get("source_refs", []),
        ))
    return sorted(artifacts, key=lambda a: (a.start_s, a.end_s, a.kind))


def get_artifacts(media_id: str, kind: Optional[str] = None, scope: str = "public") -> list[DerivedArtifact]:
    """Get artifacts for a media asset.

    `scope="public"` returns the clean artifact package from the canonical pipeline
    result. `scope="trace"` returns the low-level technical trace bundle.
    """
    normalized_scope = (scope or "public").strip().lower()
    result_file = PIPELINE_RESULTS_DIR / f"{media_id}.json"

    if normalized_scope != "trace" and result_file.exists():
        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
            artifacts_data = payload.get("artifacts", [])
            if artifacts_data:
                return _deserialize_artifacts(artifacts_data, kind=kind)
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    bundle_file = ARTIFACTS_DIR / f"{media_id}.json"
    if bundle_file.exists():
        try:
            payload = json.loads(bundle_file.read_text(encoding="utf-8"))
            return _deserialize_artifacts(payload.get("artifacts", []), kind=kind)
        except (json.JSONDecodeError, OSError, KeyError):
            return []

    if normalized_scope == "trace" and result_file.exists():
        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
            artifacts_data = payload.get("artifacts", [])
            if artifacts_data:
                return _deserialize_artifacts(artifacts_data, kind=kind)
        except (json.JSONDecodeError, OSError, KeyError):
            return []

    artifact_dir = ARTIFACTS_DIR / media_id
    if not artifact_dir.exists():
        return []
    artifacts = []
    for f in sorted(artifact_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if kind and data.get("kind") != kind:
            continue
        artifacts.append(DerivedArtifact(
            artifact_id=data["artifact_id"],
            media_id=data["media_id"],
            kind=data.get("kind", ""),
            start_s=data.get("start_s", 0.0),
            end_s=data.get("end_s", 0.0),
            content=data.get("content", ""),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            source_refs=data.get("source_refs", []),
        ))
    return sorted(artifacts, key=lambda a: a.start_s)
