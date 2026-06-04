"""Adaptive per-source audio quality profiles for live transcription.

The streaming path has to adapt to each microphone instead of relying on one
global VAD/no-speech policy.  This module keeps lightweight EWMA statistics per
source, derives a deterministic VAD profile, and consumes Twin feedback events
so bad transcript outcomes tighten the source gate over time.
"""

from __future__ import annotations

import audioop
import json
import logging
import math
import os
import re
import statistics
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

logger = logging.getLogger("archivist.source_quality")

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2
FRAME_MS = 20
FRAME_BYTES = SAMPLE_RATE * FRAME_MS // 1000 * BYTES_PER_SAMPLE

BASE_AGGRESSIVENESS = int(os.getenv("STREAMING_VAD_AGGRESSIVENESS", "2"))
BASE_MIN_UTTERANCE_MS = int(os.getenv("STREAMING_MIN_UTTERANCE_MS", "400"))
BASE_MAX_UTTERANCE_MS = int(os.getenv("STREAMING_MAX_UTTERANCE_MS", "15000"))
BASE_HANGOVER_MS = int(os.getenv("STREAMING_HANGOVER_MS", "400"))
BASE_NO_SPEECH_THRESHOLD = float(os.getenv("STREAMING_NO_SPEECH_THRESHOLD", "0.45"))
MAX_VAD_AGGRESSIVENESS = int(os.getenv("STREAMING_MAX_VAD_AGGRESSIVENESS", "2"))
MAX_NO_SPEECH_THRESHOLD = float(os.getenv("STREAMING_MAX_NO_SPEECH_THRESHOLD", "0.80"))
ALLOW_FALLBACK_ENV = (os.getenv("STREAMING_ALLOW_VAD_FALLBACK") or "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
QUALITY_DROP_THRESHOLD = float(os.getenv("STREAMING_SOURCE_QUALITY_DROP_THRESHOLD", "0.0"))
FEEDBACK_GROUP = os.getenv("SOURCE_QUALITY_FEEDBACK_GROUP", "archivist-source-quality")
FEEDBACK_CONSUMER = os.getenv("SOURCE_QUALITY_FEEDBACK_CONSUMER", "archivist")

_HALLUCINATION_PATTERNS = [
    re.compile(r"(.{8,}?)\1{2,}", re.IGNORECASE),
    re.compile(r"^\s*(so|you|oh|okay|alright|thank you)\s*\.?\s*$", re.IGNORECASE),
    re.compile(r"^\s*i'?m\s+going\s+to\s+go\s+to\s+the\s+(bathroom|next\s+video|next\s+episode)\b", re.IGNORECASE),
    re.compile(r"^\s*i'?m\s+going\s+to\s+go\s+ahead\s+and\s+(close|get\s+started)\b", re.IGNORECASE),
    re.compile(r"^\s*i\s+need\s+a\s+hug\b", re.IGNORECASE),
    re.compile(r"^\s*thanks\s+for\s+watching[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(subscribe|like\s+and\s+subscribe|don'?t\s+forget\s+to\s+subscribe)\b", re.IGNORECASE),
    re.compile(r"^\s*please\s+subscribe\b", re.IGNORECASE),
    re.compile(r"^\s*the\s+end\.{0,4}\s*$", re.IGNORECASE),
    re.compile(r"^\s*the\.{0,4}\s*$", re.IGNORECASE),
]


@dataclass(frozen=True)
class VadProfile:
    aggressiveness: int = BASE_AGGRESSIVENESS
    min_utterance_ms: int = BASE_MIN_UTTERANCE_MS
    max_utterance_ms: int = BASE_MAX_UTTERANCE_MS
    hangover_ms: int = BASE_HANGOVER_MS
    no_speech_threshold: float = BASE_NO_SPEECH_THRESHOLD
    allow_fallback: bool = False
    vad_filter: bool = False
    reason: str = "baseline"

    def key(self) -> tuple:
        return (
            self.aggressiveness,
            self.min_utterance_ms,
            self.max_utterance_ms,
            self.hangover_ms,
            round(float(self.no_speech_threshold), 3),
            bool(self.allow_fallback),
            bool(self.vad_filter),
        )


@dataclass
class SourceProfile:
    source_id: str
    kind: str = ""
    location: str = ""
    observations: int = 0
    ewma_rms_dbfs: Optional[float] = None
    ewma_peak_dbfs: Optional[float] = None
    ewma_noise_floor_dbfs: Optional[float] = None
    ewma_speech_rms_dbfs: Optional[float] = None
    ewma_snr_db: Optional[float] = None
    ewma_active_fraction: Optional[float] = None
    ewma_clip_fraction: Optional[float] = None
    quality_score: float = 0.0
    transcript_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    hallucination_count: int = 0
    fallback_count: int = 0
    feedback_count: int = 0
    last_drop_reason: str = ""
    last_text: str = ""
    last_observed_at: float = 0.0
    vad_profile: VadProfile = field(default_factory=VadProfile)

    def update_audio(self, stats: dict[str, Any], *, kind: str = "", location: str = "") -> None:
        if kind:
            self.kind = kind
        if location:
            self.location = location
        self.observations += 1
        self.last_observed_at = time.time()
        alpha = 0.12 if self.observations > 4 else 0.35

        def ewma(field_name: str, incoming: Any) -> None:
            try:
                value = float(incoming)
            except Exception:
                return
            previous = getattr(self, field_name)
            if previous is None:
                setattr(self, field_name, value)
            else:
                setattr(self, field_name, (float(previous) * (1.0 - alpha)) + (value * alpha))

        ewma("ewma_rms_dbfs", stats.get("rms_dbfs"))
        ewma("ewma_peak_dbfs", stats.get("peak_dbfs"))
        ewma("ewma_noise_floor_dbfs", stats.get("noise_floor_dbfs"))
        ewma("ewma_speech_rms_dbfs", stats.get("speech_rms_dbfs"))
        ewma("ewma_snr_db", stats.get("snr_db"))
        ewma("ewma_active_fraction", stats.get("active_frame_fraction"))
        ewma("ewma_clip_fraction", stats.get("clip_fraction"))
        self.quality_score = _quality_score(
            snr_db=self.ewma_snr_db,
            rms_dbfs=self.ewma_rms_dbfs,
            active_fraction=self.ewma_active_fraction,
            clip_fraction=self.ewma_clip_fraction,
        )
        self.vad_profile = _derive_vad_profile(self)

    def update_transcript(
        self,
        text: str,
        meta: dict[str, Any] | None,
        *,
        accepted: bool,
        drop_reason: str = "",
    ) -> None:
        self.transcript_count += 1
        self.last_text = str(text or "")[:180]
        self.last_observed_at = time.time()
        meta = meta or {}
        if bool(meta.get("fallback")):
            self.fallback_count += 1
        hallucinated = _looks_like_hallucination(text)
        if hallucinated:
            self.hallucination_count += 1
        if accepted:
            self.accepted_count += 1
            self.last_drop_reason = ""
        else:
            self.rejected_count += 1
            self.last_drop_reason = drop_reason or ("hallucination" if hallucinated else "source_gate")
        self.vad_profile = _derive_vad_profile(self)

    def update_feedback(self, payload: dict[str, Any]) -> None:
        self.feedback_count += 1
        outcome = str(payload.get("outcome") or payload.get("status") or "").strip().lower()
        if outcome in {"hallucination_drop", "filtered_hallucination"}:
            self.hallucination_count += 1
            self.rejected_count += 1
            self.last_drop_reason = outcome
        elif outcome in {"low_quality_drop", "twin_quality_gate"}:
            self.rejected_count += 1
            self.last_drop_reason = outcome
        elif outcome in {"accepted_for_pipeline", "wake", "direct_wake", "verified_success", "command_executed"}:
            self.accepted_count += 1
            self.last_drop_reason = ""
        elif outcome in {"failed", "partial", "execution_failed"}:
            self.rejected_count += 1
            self.last_drop_reason = outcome
        self.vad_profile = _derive_vad_profile(self)

    def snapshot(self) -> dict[str, Any]:
        total = max(1, int(self.transcript_count + self.feedback_count))
        hallucination_rate = round(float(self.hallucination_count) / total, 4)
        rejection_rate = round(float(self.rejected_count) / max(1, self.transcript_count + self.rejected_count), 4)
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "location": self.location,
            "observations": self.observations,
            "quality_score": round(float(self.quality_score), 3),
            "rms_dbfs": _round_or_none(self.ewma_rms_dbfs),
            "peak_dbfs": _round_or_none(self.ewma_peak_dbfs),
            "noise_floor_dbfs": _round_or_none(self.ewma_noise_floor_dbfs),
            "speech_rms_dbfs": _round_or_none(self.ewma_speech_rms_dbfs),
            "snr_db": _round_or_none(self.ewma_snr_db),
            "active_frame_fraction": _round_or_none(self.ewma_active_fraction, digits=3),
            "clip_fraction": _round_or_none(self.ewma_clip_fraction, digits=5),
            "transcript_count": self.transcript_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "hallucination_count": self.hallucination_count,
            "hallucination_rate": hallucination_rate,
            "rejection_rate": rejection_rate,
            "fallback_count": self.fallback_count,
            "feedback_count": self.feedback_count,
            "last_drop_reason": self.last_drop_reason,
            "last_text": self.last_text,
            "last_observed_at": self.last_observed_at,
            "vad_profile": asdict(self.vad_profile),
        }


_profiles: dict[str, SourceProfile] = {}
_lock = threading.Lock()
_feedback_thread: Optional[threading.Thread] = None
_feedback_stop = threading.Event()


def _round_or_none(value: Optional[float], *, digits: int = 1) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _dbfs(amplitude: float, *, full_scale: float = 32768.0) -> float:
    if amplitude <= 0:
        return -120.0
    return max(-120.0, 20.0 * math.log10(float(amplitude) / float(full_scale)))


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return -120.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return float(ordered[idx])


def audio_quality_stats(pcm: bytes) -> dict[str, Any]:
    usable = pcm[: len(pcm) - (len(pcm) % 2)] if pcm else b""
    if not usable:
        return {
            "samples": 0,
            "rms": 0.0,
            "peak": 0.0,
            "rms_dbfs": -120.0,
            "peak_dbfs": -120.0,
            "noise_floor_dbfs": -120.0,
            "speech_rms_dbfs": -120.0,
            "snr_db": 0.0,
            "active_frame_fraction": 0.0,
            "clip_fraction": 0.0,
            "near_clip_fraction": 0.0,
        }
    try:
        rms = float(audioop.rms(usable, 2))
        peak = float(audioop.max(usable, 2))
        clip_count = 0
        near_clip_count = 0
        sample_count = len(usable) // 2
        for idx in range(0, len(usable), 2):
            sample = int.from_bytes(usable[idx : idx + 2], "little", signed=True)
            abs_sample = abs(sample)
            if abs_sample >= 32700:
                clip_count += 1
            if abs_sample >= 29491:  # ~90% full scale
                near_clip_count += 1
    except Exception:
        rms = 0.0
        peak = 0.0
        sample_count = len(usable) // 2
        clip_count = 0
        near_clip_count = 0

    frame_dbfs: list[float] = []
    for offset in range(0, len(usable) - FRAME_BYTES + 1, FRAME_BYTES):
        frame = usable[offset : offset + FRAME_BYTES]
        try:
            frame_dbfs.append(_dbfs(float(audioop.rms(frame, 2))))
        except Exception:
            frame_dbfs.append(-120.0)
    if not frame_dbfs:
        frame_dbfs = [_dbfs(rms)]

    noise_floor = _percentile(frame_dbfs, 10)
    speech_rms = _percentile(frame_dbfs, 95)
    snr = max(0.0, speech_rms - noise_floor)
    active_threshold = max(noise_floor + 8.0, -50.0)
    active_count = sum(1 for value in frame_dbfs if value >= active_threshold)
    active_fraction = active_count / max(1, len(frame_dbfs))

    return {
        "samples": sample_count,
        "rms": round(rms / 32768.0, 6),
        "peak": round(peak / 32768.0, 6),
        "rms_dbfs": round(_dbfs(rms), 1),
        "peak_dbfs": round(_dbfs(peak), 1),
        "noise_floor_dbfs": round(noise_floor, 1),
        "speech_rms_dbfs": round(speech_rms, 1),
        "snr_db": round(snr, 1),
        "active_frame_fraction": round(active_fraction, 3),
        "clip_fraction": round(clip_count / max(1, sample_count), 6),
        "near_clip_fraction": round(near_clip_count / max(1, sample_count), 6),
        "frame_rms_dbfs_median": round(float(statistics.median(frame_dbfs)), 1),
    }


def _quality_score(
    *,
    snr_db: Optional[float],
    rms_dbfs: Optional[float],
    active_fraction: Optional[float],
    clip_fraction: Optional[float],
) -> float:
    snr = 0.0 if snr_db is None else float(snr_db)
    rms = -120.0 if rms_dbfs is None else float(rms_dbfs)
    active = 0.0 if active_fraction is None else float(active_fraction)
    clipping = 0.0 if clip_fraction is None else float(clip_fraction)
    snr_score = min(1.0, max(0.0, (snr - 6.0) / 18.0))
    level_score = min(1.0, max(0.0, (rms + 55.0) / 32.0))
    if active < 0.02:
        active_score = 0.1
    elif active > 0.78:
        active_score = 0.45
    else:
        active_score = 1.0
    clip_penalty = min(0.7, clipping * 55.0)
    score = (0.55 * snr_score) + (0.25 * level_score) + (0.20 * active_score) - clip_penalty
    return min(1.0, max(0.0, score))


def _derive_vad_profile(profile: SourceProfile) -> VadProfile:
    snr = profile.ewma_snr_db if profile.ewma_snr_db is not None else 0.0
    clip_fraction = profile.ewma_clip_fraction if profile.ewma_clip_fraction is not None else 0.0
    total = max(1, profile.transcript_count + profile.feedback_count)
    hallucination_rate = float(profile.hallucination_count) / total
    quality = float(profile.quality_score)

    aggressiveness = BASE_AGGRESSIVENESS
    min_ms = BASE_MIN_UTTERANCE_MS
    hangover_ms = BASE_HANGOVER_MS
    threshold = BASE_NO_SPEECH_THRESHOLD
    allow_fallback = False
    vad_filter = False
    reason = "baseline"

    if clip_fraction >= 0.003:
        reason = "clipping"
        threshold = max(threshold, 0.55)
        min_ms = max(min_ms, 550)
        vad_filter = True
    if quality < 0.35 or snr < 10.0 or hallucination_rate >= 0.12:
        aggressiveness = max(aggressiveness, 2)
        min_ms = max(min_ms, 500)
        hangover_ms = max(hangover_ms, 500)
        threshold = max(threshold, 0.50)
        vad_filter = True
        reason = "strict_low_quality"
    elif quality < 0.55 or snr < 14.0:
        aggressiveness = max(aggressiveness, 2)
        min_ms = max(min_ms, 500)
        hangover_ms = max(hangover_ms, 500)
        threshold = max(threshold, 0.50)
        vad_filter = True
        reason = "guarded"
    elif ALLOW_FALLBACK_ENV and quality > 0.78 and hallucination_rate == 0.0:
        allow_fallback = True
        reason = "clean_allow_fallback"

    return VadProfile(
        aggressiveness=max(0, min(MAX_VAD_AGGRESSIVENESS, int(aggressiveness))),
        min_utterance_ms=int(min_ms),
        max_utterance_ms=int(BASE_MAX_UTTERANCE_MS),
        hangover_ms=int(hangover_ms),
        no_speech_threshold=round(min(float(threshold), MAX_NO_SPEECH_THRESHOLD), 3),
        allow_fallback=bool(allow_fallback),
        vad_filter=bool(vad_filter),
        reason=reason,
    )


def _metadata_for_source(source_id: str) -> tuple[str, str, float]:
    try:
        import sources_config

        src = sources_config.get_source(source_id)
        if src is not None:
            threshold = getattr(src.transcription, "no_speech_threshold", BASE_NO_SPEECH_THRESHOLD)
            return str(src.kind or ""), str(src.location or ""), float(threshold)
    except Exception:
        pass
    return "", "", BASE_NO_SPEECH_THRESHOLD


def _profile_for(source_id: str) -> SourceProfile:
    key = str(source_id or "unknown").strip() or "unknown"
    profile = _profiles.get(key)
    if profile is None:
        kind, location, threshold = _metadata_for_source(key)
        profile = SourceProfile(source_id=key, kind=kind, location=location)
        profile.vad_profile = VadProfile(no_speech_threshold=float(threshold), allow_fallback=False)
        _profiles[key] = profile
    return profile


def observe_audio(
    source_id: str,
    pcm: bytes,
    *,
    kind: str = "",
    location: str = "",
    stream_ts: float | None = None,
) -> dict[str, Any]:
    stats = audio_quality_stats(pcm)
    with _lock:
        profile = _profile_for(source_id)
        profile.update_audio(stats, kind=kind, location=location)
        snapshot = profile.snapshot()
    snapshot["last_audio_stats"] = stats
    if stream_ts is not None:
        snapshot["audio_stream_ts"] = stream_ts
    return snapshot


def vad_profile(source_id: str) -> VadProfile:
    with _lock:
        return _profile_for(source_id).vad_profile


def snapshot(source_id: str) -> dict[str, Any]:
    with _lock:
        return _profile_for(source_id).snapshot()


def all_snapshots() -> list[dict[str, Any]]:
    with _lock:
        return [profile.snapshot() for profile in sorted(_profiles.values(), key=lambda item: item.source_id)]


def _segment_values(segments: list[Any] | None, attr: str) -> list[float]:
    out: list[float] = []
    for segment in segments or []:
        value = None
        if isinstance(segment, dict):
            value = segment.get(attr)
        else:
            value = getattr(segment, attr, None)
        try:
            if value is not None:
                out.append(float(value))
        except Exception:
            continue
    return out


def _looks_like_hallucination(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return True
    for pattern in _HALLUCINATION_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def transcript_decision(
    source_id: str,
    text: str,
    meta: dict[str, Any] | None,
    segments: list[Any] | None,
) -> tuple[bool, str, dict[str, Any]]:
    meta = meta or {}
    with _lock:
        profile = _profile_for(source_id)
        profile_snapshot = profile.snapshot()
        current_vad = profile.vad_profile
    max_no_speech = meta.get("max_no_speech_prob", meta.get("no_speech_prob"))
    if max_no_speech is None:
        values = _segment_values(segments, "no_speech_prob")
        max_no_speech = max(values) if values else None
    try:
        no_speech = float(max_no_speech) if max_no_speech is not None else None
    except Exception:
        no_speech = None

    accepted = True
    reason = ""
    if not str(text or "").strip():
        accepted = False
        reason = "empty_transcript"
    elif _looks_like_hallucination(text):
        accepted = False
        reason = "hallucination_pattern"
    elif no_speech is not None and no_speech >= current_vad.no_speech_threshold:
        accepted = False
        reason = f"no_speech_prob:{no_speech:.2f}"
    elif bool(meta.get("fallback")) and not current_vad.allow_fallback:
        accepted = False
        reason = "vad_fallback_disabled"
    elif profile_snapshot.get("quality_score", 0.0) < QUALITY_DROP_THRESHOLD:
        accepted = False
        reason = f"source_quality:{profile_snapshot.get('quality_score', 0.0):.2f}"

    with _lock:
        profile = _profile_for(source_id)
        profile.update_transcript(text, meta, accepted=accepted, drop_reason=reason)
        profile_snapshot = profile.snapshot()
    return accepted, reason, profile_snapshot


def observe_feedback(source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        profile = _profile_for(source_id)
        profile.update_feedback(payload)
        return profile.snapshot()


def _handle_feedback(_topic: str, _entry_id: str, parsed: dict[str, Any]) -> None:
    source_id = str(parsed.get("source") or "").strip()
    payload = parsed.get("payload") if isinstance(parsed.get("payload"), dict) else {}
    if not source_id:
        return
    snapshot_data = observe_feedback(source_id, payload)
    logger.debug(
        "source feedback applied source=%s outcome=%s profile=%s",
        source_id,
        payload.get("outcome"),
        snapshot_data.get("vad_profile", {}).get("reason"),
    )


def start_feedback_consumer() -> None:
    global _feedback_thread
    if _feedback_thread is not None and _feedback_thread.is_alive():
        return
    _feedback_stop.clear()

    def _loop() -> None:
        try:
            import events_bus

            events_bus.consume(
                topics=("source.feedback",),
                group=FEEDBACK_GROUP,
                consumer=FEEDBACK_CONSUMER,
                handler=_handle_feedback,
                stop_event=_feedback_stop,
                block_ms=2000,
                batch=16,
            )
        except Exception:
            logger.exception("source-quality feedback consumer stopped")

    _feedback_thread = threading.Thread(target=_loop, daemon=True, name="source-quality-feedback")
    _feedback_thread.start()
    logger.info("source-quality feedback consumer started")


def stop_feedback_consumer(timeout: float = 2.0) -> None:
    _feedback_stop.set()
    if _feedback_thread is not None:
        _feedback_thread.join(timeout=timeout)


def reset_for_tests() -> None:
    with _lock:
        _profiles.clear()
    _feedback_stop.set()
