"""L0: Raw evidence store - register and manage media assets and derived artifacts."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from media.models import DerivedArtifact, MediaAsset, Modality, PipelineJob

logger = logging.getLogger("archivist.media.evidence")

MEDIA_STORE_DIR = Path(os.getenv("MEDIA_STORE_DIR", "/data/media_store"))
ASSETS_INDEX = MEDIA_STORE_DIR / "assets.json"
ARTIFACTS_DIR = MEDIA_STORE_DIR / "artifacts"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".wma", ".aac", ".webm"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".ts", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"}
ALL_MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS | IMAGE_EXTS


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
    """Use ffprobe to extract media metadata."""
    try:
        import ffmpeg as ffmpeg_lib
        probe = ffmpeg_lib.probe(path)
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

    modality = _detect_modality(path)
    probe_info = _probe_media(path) if modality in (Modality.AUDIO, Modality.VIDEO) else {}

    asset = MediaAsset(
        path=str(file_path.resolve()),
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
        metadata=metadata or {},
    )
    asset.compute_hash()

    _save_asset(asset)
    logger.info("Registered media asset: %s (%s, %.1fs)", asset.filename, asset.modality, asset.duration_s)
    return asset


def _save_asset(asset: MediaAsset):
    """Persist asset metadata to the store."""
    MEDIA_STORE_DIR.mkdir(parents=True, exist_ok=True)
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
    ASSETS_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _load_assets_index() -> dict:
    if ASSETS_INDEX.exists():
        try:
            return json.loads(ASSETS_INDEX.read_text(encoding="utf-8"))
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
    """Save a derived artifact."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_dir = ARTIFACTS_DIR / artifact.media_id
    artifact_dir.mkdir(exist_ok=True)
    artifact_file = artifact_dir / f"{artifact.artifact_id}.json"
    artifact_file.write_text(json.dumps({
        "artifact_id": artifact.artifact_id,
        "media_id": artifact.media_id,
        "kind": artifact.kind,
        "start_s": artifact.start_s,
        "end_s": artifact.end_s,
        "content": artifact.content,
        "confidence": artifact.confidence,
        "metadata": artifact.metadata,
        "source_refs": artifact.source_refs,
    }, indent=2), encoding="utf-8")


def get_artifacts(media_id: str, kind: Optional[str] = None) -> list[DerivedArtifact]:
    """Get all artifacts for a media asset, optionally filtered by kind."""
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
