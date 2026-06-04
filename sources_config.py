"""Source configuration loader for archivist's unified media pipeline.

Loads /app/config/sources.yml (or ARCHIVIST_SOURCES_CONFIG), returns typed
Source records, supports mtime-based hot reload. Phase 1 callers need only
enabled_sources().
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger("archivist.sources")

DEFAULT_CONFIG_PATH = os.getenv("ARCHIVIST_SOURCES_CONFIG", "/app/config/sources.yml")


@dataclass(frozen=True)
class DetectProfile:
    width: int = 704
    height: int = 480
    fps: int = 10


@dataclass(frozen=True)
class MotionProfile:
    threshold: int = 40
    contour_area: int = 10
    improve_contrast: bool = True
    mask: tuple[float, ...] = ()


@dataclass(frozen=True)
class AudioProfile:
    sample_rate: int = 16000
    channels: int = 1


@dataclass(frozen=True)
class TranscriptionProfile:
    enabled: bool = True
    no_speech_threshold: float = 0.5


@dataclass(frozen=True)
class RetentionProfile:
    """Per-source staging + archival policy.

    Flow (wall-clock age since segment close):
      0 .. local_hold_hours        → segment on local SSD (sonic) staging
      local_hold_hours .. nas_continuous_days  → on NAS (megamind), kept regardless of labels
      nas_continuous_days .. nas_event_days    → on NAS, kept ONLY if labels ∩ keep_labels
      > nas_event_days              → deleted
    """
    local_hold_hours: float = 48.0
    nas_continuous_days: float = 30.0
    nas_event_days: float = 365.0
    keep_labels: tuple[str, ...] = ("motion", "person", "car", "truck", "speech")


@dataclass(frozen=True)
class Source:
    id: str
    enabled: bool
    kind: str                       # "camera" | "mic"
    location: str
    audio_url: Optional[str]
    video_main_url: Optional[str]
    video_sub_url: Optional[str]
    rtsp_transport: str
    reconnect_min_s: float
    reconnect_max_s: float
    detect: DetectProfile
    motion: Optional[MotionProfile]
    zones: dict[str, tuple[float, ...]] = field(default_factory=dict)
    audio: AudioProfile = field(default_factory=AudioProfile)
    transcription: TranscriptionProfile = field(default_factory=TranscriptionProfile)
    retention: RetentionProfile = field(default_factory=RetentionProfile)
    segment_format: str = "mp4"     # "mp4" | "mpegts" — mpegts for streams MP4 rejects


_lock = threading.Lock()
_cache: dict[str, Source] = {}
_cache_mtime: float = 0.0
_cache_path: Optional[Path] = None


def _as_tuple(value) -> tuple[float, ...]:
    if not value:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(float(x) for x in value)
    raise TypeError(f"expected list/tuple of floats, got {type(value).__name__}")


def _detect_from_dict(d: Optional[dict]) -> DetectProfile:
    d = d or {}
    return DetectProfile(
        width=int(d.get("width", 704)),
        height=int(d.get("height", 480)),
        fps=int(d.get("fps", 10)),
    )


def _motion_from_dict(d: Optional[dict]) -> Optional[MotionProfile]:
    if not d:
        return None
    return MotionProfile(
        threshold=int(d.get("threshold", 40)),
        contour_area=int(d.get("contour_area", 10)),
        improve_contrast=bool(d.get("improve_contrast", True)),
        mask=_as_tuple(d.get("mask")),
    )


def _audio_from_dict(d: Optional[dict]) -> AudioProfile:
    d = d or {}
    return AudioProfile(
        sample_rate=int(d.get("sample_rate", 16000)),
        channels=int(d.get("channels", 1)),
    )


def _transcription_from_dict(d: Optional[dict]) -> TranscriptionProfile:
    d = d or {}
    return TranscriptionProfile(
        enabled=bool(d.get("enabled", True)),
        no_speech_threshold=float(d.get("no_speech_threshold", 0.5)),
    )


def _retention_from_dict(d: Optional[dict]) -> RetentionProfile:
    d = d or {}
    raw_labels = d.get("keep_labels")
    if isinstance(raw_labels, str):
        labels = tuple(s.strip() for s in raw_labels.split(",") if s.strip())
    elif isinstance(raw_labels, (list, tuple)):
        labels = tuple(str(s).strip() for s in raw_labels if str(s).strip())
    else:
        labels = ("motion", "person", "car", "truck", "speech")
    return RetentionProfile(
        local_hold_hours=float(d.get("local_hold_hours", 48.0)),
        nas_continuous_days=float(d.get("nas_continuous_days", 30.0)),
        nas_event_days=float(d.get("nas_event_days", 365.0)),
        keep_labels=labels,
    )


def _build_source(entry: dict, defaults: dict) -> Source:
    src_id = str(entry["id"])
    zones_raw = entry.get("zones") or {}
    zones = {k: _as_tuple(v) for k, v in zones_raw.items()}
    return Source(
        id=src_id,
        enabled=bool(entry.get("enabled", False)),
        kind=str(entry.get("kind", "camera")),
        location=str(entry.get("location", src_id)),
        audio_url=entry.get("audio_url"),
        video_main_url=entry.get("video_main_url"),
        video_sub_url=entry.get("video_sub_url"),
        rtsp_transport=str(entry.get("rtsp_transport", defaults.get("rtsp_transport", "tcp"))),
        reconnect_min_s=float(entry.get("reconnect_min_s", defaults.get("reconnect_min_s", 2))),
        reconnect_max_s=float(entry.get("reconnect_max_s", defaults.get("reconnect_max_s", 60))),
        detect=_detect_from_dict(entry.get("detect")),
        motion=_motion_from_dict(entry.get("motion")),
        zones=zones,
        audio=_audio_from_dict({**(defaults.get("audio") or {}), **(entry.get("audio") or {})}),
        transcription=_transcription_from_dict(
            {**(defaults.get("transcription") or {}), **(entry.get("transcription") or {})}
        ),
        retention=_retention_from_dict(
            {**(defaults.get("retention") or {}), **(entry.get("retention") or {})}
        ),
        segment_format=str(entry.get("segment_format", defaults.get("segment_format", "mp4"))).lower(),
    )


def load_sources(path: Optional[str] = None, force: bool = False) -> dict[str, Source]:
    """Load (or reload on mtime change) sources from YAML. Returns id→Source dict."""
    global _cache, _cache_mtime, _cache_path
    resolved = Path(path or DEFAULT_CONFIG_PATH)
    with _lock:
        try:
            mtime = resolved.stat().st_mtime
        except FileNotFoundError:
            logger.warning("sources config not found at %s", resolved)
            _cache, _cache_mtime, _cache_path = {}, 0.0, resolved
            return _cache
        if not force and _cache_path == resolved and mtime == _cache_mtime and _cache:
            return _cache
        with resolved.open("r") as f:
            raw = yaml.safe_load(f) or {}
        defaults = raw.get("defaults") or {}
        entries = raw.get("sources") or []
        sources: dict[str, Source] = {}
        for entry in entries:
            try:
                src = _build_source(entry, defaults)
            except Exception:
                logger.exception("bad source entry: %r", entry)
                continue
            if src.id in sources:
                logger.warning("duplicate source id %s, keeping first", src.id)
                continue
            sources[src.id] = src
        _cache, _cache_mtime, _cache_path = sources, mtime, resolved
        logger.info(
            "loaded %d sources from %s (%d enabled)",
            len(sources),
            resolved,
            sum(1 for s in sources.values() if s.enabled),
        )
        return _cache


def enabled_sources(path: Optional[str] = None) -> list[Source]:
    return [s for s in load_sources(path).values() if s.enabled]


def get_source(src_id: str, path: Optional[str] = None) -> Optional[Source]:
    return load_sources(path).get(src_id)
