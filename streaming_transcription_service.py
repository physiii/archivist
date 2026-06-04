"""Streaming transcription service.

Consumes per-source PCM (int16 mono 16kHz) from rtsp_ingest_service, runs
webrtcvad in 20ms frames to detect utterance boundaries, buffers speech into
an utterance, and when the utterance closes calls
transcription_service.transcribe_audio_bytes(wav_bytes). Emits:

  - transcript.final   {text, start_ts, end_ts, segments, lang, no_speech_prob}

Per-source queues are bounded; when full we drop-oldest (never block the ingest
thread). Whisper is semaphore-gated inside transcription_service already, so
only one transcription runs at a time globally.

Phase 1 deliberately skips transcript.partial — rolling-window stabilization
adds complexity and cost. We revisit once the baseline is proven.
"""

from __future__ import annotations

import collections
import io
import logging
import os
import struct
import threading
import time
import wave
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Optional

import events_bus
import source_quality

logger = logging.getLogger("archivist.streaming")

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # int16 mono
VAD_FRAME_MS = 20
VAD_FRAME_BYTES = SAMPLE_RATE * VAD_FRAME_MS // 1000 * BYTES_PER_SAMPLE  # 640 bytes @ 16kHz

AGGRESSIVENESS = int(os.getenv("STREAMING_VAD_AGGRESSIVENESS", "2"))
MIN_UTTERANCE_MS = int(os.getenv("STREAMING_MIN_UTTERANCE_MS", "400"))
MAX_UTTERANCE_MS = int(os.getenv("STREAMING_MAX_UTTERANCE_MS", "15000"))
HANGOVER_MS = int(os.getenv("STREAMING_HANGOVER_MS", "400"))
QUEUE_MAX = int(os.getenv("STREAMING_QUEUE_MAX", "200"))
KEEPALIVE_SECS = int(os.getenv("STREAMING_KEEPALIVE_SECS", "300"))
AUTO_GAIN_THRESHOLD_DBFS = float(os.getenv("STREAMING_AUTO_GAIN_THRESHOLD_DBFS", "-45"))
AUTO_GAIN_TARGET_DBFS = float(os.getenv("STREAMING_AUTO_GAIN_TARGET_DBFS", "-28"))
AUTO_GAIN_MAX = float(os.getenv("STREAMING_AUTO_GAIN_MAX", "16.0"))


@dataclass
class _SourceState:
    source_id: str
    queue: Queue
    thread: threading.Thread
    dropped: int = 0
    submitted: int = 0


_states: dict[str, _SourceState] = {}
_state_lock = threading.Lock()
_stop_event = threading.Event()


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(BYTES_PER_SAMPLE)
        w.setframerate(sample_rate)
        w.writeframes(pcm_bytes)
    return buf.getvalue()


class _VadSegmenter:
    """Simple VAD-driven utterance segmenter.

    Consumes arbitrary-length PCM input, yields (pcm_bytes, start_stream_ts,
    end_stream_ts) tuples per closed utterance.
    """

    def __init__(self, aggressiveness: int = AGGRESSIVENESS, profile: source_quality.VadProfile | None = None):
        import webrtcvad  # local import; only this class needs it

        self.profile = profile or source_quality.VadProfile(aggressiveness=aggressiveness)
        self._vad = webrtcvad.Vad(aggressiveness)
        self._residual = b""
        self._speech = bytearray()
        self._in_speech = False
        self._silence_ms = 0
        self._speech_ms = 0
        self._start_ts: Optional[float] = None
        self._last_ts: Optional[float] = None

    @property
    def in_speech(self) -> bool:
        return bool(self._in_speech)

    def feed(self, pcm: bytes, stream_ts: Optional[float]):
        """Feed raw int16 mono 16kHz PCM. Returns a list of closed utterances."""
        out = []
        if stream_ts is not None:
            # stream_ts marks the start of this chunk's first sample.
            self._last_ts = stream_ts
        buf = self._residual + pcm
        self._residual = b""
        i = 0
        while i + VAD_FRAME_BYTES <= len(buf):
            frame = buf[i : i + VAD_FRAME_BYTES]
            i += VAD_FRAME_BYTES
            is_speech = False
            try:
                is_speech = self._vad.is_speech(frame, SAMPLE_RATE)
            except Exception:
                is_speech = False
            if is_speech:
                if not self._in_speech:
                    self._in_speech = True
                    self._start_ts = self._last_ts
                    self._speech.clear()
                    self._speech_ms = 0
                self._speech.extend(frame)
                self._speech_ms += VAD_FRAME_MS
                self._silence_ms = 0
                if self._speech_ms >= self.profile.max_utterance_ms:
                    out.append(self._close_utterance())
            else:
                if self._in_speech:
                    # include a bit of trailing silence so words don't clip
                    self._speech.extend(frame)
                    self._silence_ms += VAD_FRAME_MS
                    if self._silence_ms >= self.profile.hangover_ms:
                        if self._speech_ms >= self.profile.min_utterance_ms:
                            out.append(self._close_utterance())
                        else:
                            # too short; discard
                            self._reset()
        self._residual = buf[i:]
        return out

    def _close_utterance(self):
        pcm = bytes(self._speech)
        start = self._start_ts
        # end = start + speech_ms. If we don't have ts, caller falls back to wall time.
        end = (start + (self._speech_ms / 1000.0)) if start is not None else None
        self._reset()
        return pcm, start, end

    def _reset(self):
        self._speech.clear()
        self._speech_ms = 0
        self._silence_ms = 0
        self._in_speech = False
        self._start_ts = None


def _auto_gain_pcm(pcm: bytes, source_id: str) -> bytes:
    """Boost quiet sources so WebRTC VAD can detect speech."""
    import audioop
    try:
        profile = source_quality._profile_for(source_id)
        rms_dbfs = profile.ewma_rms_dbfs
        if rms_dbfs is None or rms_dbfs > AUTO_GAIN_THRESHOLD_DBFS:
            return pcm
        gain_db = AUTO_GAIN_TARGET_DBFS - rms_dbfs
        gain = min(AUTO_GAIN_MAX, 10.0 ** (gain_db / 20.0))
        if gain <= 1.05:
            return pcm
        return audioop.mul(pcm, BYTES_PER_SAMPLE, gain)
    except Exception:
        return pcm


def _source_loop(state: _SourceState, transcribe_fn):
    profile = source_quality.vad_profile(state.source_id)
    segmenter = _VadSegmenter(profile.aggressiveness, profile=profile)
    profile_key = profile.key()
    while not _stop_event.is_set():
        try:
            item = state.queue.get(timeout=0.5)
        except Empty:
            continue
        if item is None:  # sentinel
            break
        pcm, stream_ts = item
        pcm = _auto_gain_pcm(pcm, state.source_id)
        latest_profile = source_quality.vad_profile(state.source_id)
        latest_key = latest_profile.key()
        if latest_key != profile_key and not segmenter.in_speech:
            logger.info(
                "source %s VAD profile changed: %s",
                state.source_id,
                latest_profile,
            )
            segmenter = _VadSegmenter(latest_profile.aggressiveness, profile=latest_profile)
            profile = latest_profile
            profile_key = latest_key
        utterances = segmenter.feed(pcm, stream_ts)
        for u_pcm, u_start, u_end in utterances:
            _transcribe_and_publish(state, u_pcm, u_start, u_end, transcribe_fn)


def _transcribe_and_publish(state, pcm, start_ts, end_ts, transcribe_fn):
    if not pcm:
        return
    wav = _pcm_to_wav(pcm)
    utterance_quality = source_quality.audio_quality_stats(pcm)
    vad_profile = source_quality.vad_profile(state.source_id)
    t0 = time.time()
    try:
        text, meta, segments = transcribe_fn(
            wav,
            content_type="audio/wav",
            filename=f"{state.source_id}_stream.wav",
            vad_filter=vad_profile.vad_filter,
            allow_fallback=vad_profile.allow_fallback,
            no_speech_threshold=vad_profile.no_speech_threshold,
        )
    except Exception:
        logger.exception("transcription failed for %s", state.source_id)
        return
    elapsed = time.time() - t0
    text = (text or "").strip()
    accepted, drop_reason, quality_snapshot = source_quality.transcript_decision(
        state.source_id,
        text,
        meta or {},
        segments or [],
    )
    if not text or not accepted:
        events_bus.publish(
            "source.health",
            state.source_id,
            {
                "state": "up",
                "role": "audio",
                "audio_state": "transcript_dropped",
                "drop_reason": drop_reason or "empty_transcript",
                "source_quality": quality_snapshot,
                "vad_profile": quality_snapshot.get("vad_profile"),
            },
        )
        return
    state.submitted += 1
    seg_out = []
    for s in segments or []:
        if isinstance(s, dict):
            seg_out.append({
                "t0": float(s.get("start") or 0.0),
                "t1": float(s.get("end") or 0.0),
                "text": (s.get("text") or "").strip(),
                "avg_logprob": s.get("avg_logprob"),
                "no_speech_prob": s.get("no_speech_prob"),
                "compression_ratio": s.get("compression_ratio"),
            })
        else:
            seg_out.append({
                "t0": float(getattr(s, "start", 0.0) or 0.0),
                "t1": float(getattr(s, "end", 0.0) or 0.0),
                "text": (getattr(s, "text", "") or "").strip(),
                "avg_logprob": getattr(s, "avg_logprob", None),
                "no_speech_prob": getattr(s, "no_speech_prob", None),
                "compression_ratio": getattr(s, "compression_ratio", None),
            })
    events_bus.publish(
        "transcript.final",
        state.source_id,
        {
            "text": text,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "lang": (meta or {}).get("lang") or (meta or {}).get("language"),
            "no_speech_prob": (meta or {}).get("max_no_speech_prob") or (meta or {}).get("no_speech_prob"),
            "avg_logprob": (meta or {}).get("avg_logprob"),
            "audio_stats": (meta or {}).get("audio_stats"),
            "utterance_audio_quality": utterance_quality,
            "source_quality": quality_snapshot,
            "vad_profile": quality_snapshot.get("vad_profile"),
            "accepted_by_source_gate": True,
            "segments": seg_out,
            "inference_s": round(elapsed, 3),
        },
    )


def _default_transcribe_fn():
    import transcription_service

    return transcription_service.transcribe_audio_bytes


def enqueue_audio(source_id: str, pcm_bytes: bytes, stream_ts: Optional[float]) -> None:
    """Called by the RTSP ingest thread for every decoded PCM chunk."""
    source_quality.observe_audio(source_id, pcm_bytes, stream_ts=stream_ts)
    state = _states.get(source_id)
    if state is None:
        state = _ensure_state(source_id, _default_transcribe_fn())
    try:
        state.queue.put_nowait((pcm_bytes, stream_ts))
    except Exception:
        # drop-oldest
        try:
            state.queue.get_nowait()
            state.dropped += 1
        except Exception:
            pass
        try:
            state.queue.put_nowait((pcm_bytes, stream_ts))
        except Exception:
            state.dropped += 1


def _ensure_state(source_id: str, transcribe_fn) -> _SourceState:
    with _state_lock:
        existing = _states.get(source_id)
        if existing is not None:
            return existing
        q: Queue = Queue(maxsize=QUEUE_MAX)
        t = threading.Thread(
            target=_source_loop,
            args=(None, transcribe_fn),  # state filled in below before thread runs loop
            daemon=True,
            name=f"streaming-txr-{source_id}",
        )
        state = _SourceState(source_id=source_id, queue=q, thread=t)
        # rebind target with the now-existing state object
        t_target = lambda s=state, fn=transcribe_fn: _source_loop(s, fn)
        new_thread = threading.Thread(
            target=t_target,
            daemon=True,
            name=f"streaming-txr-{source_id}",
        )
        state.thread = new_thread
        _states[source_id] = state
        new_thread.start()
        logger.info("started streaming transcription worker for %s", source_id)
        return state


def start_all(transcribe_fn=None) -> None:
    """Pre-create workers for all enabled sources. Safe to call multiple times."""
    import sources_config

    fn = transcribe_fn or _default_transcribe_fn()
    _stop_event.clear()
    source_quality.start_feedback_consumer()
    for src in sources_config.enabled_sources():
        if not src.transcription.enabled:
            continue
        source_quality.snapshot(src.id)
        _ensure_state(src.id, fn)
    _start_keepalive()


_keepalive_thread: Optional[threading.Thread] = None


def _start_keepalive() -> None:
    """Periodic silent transcribe to keep whisper's CUDA context / kernels hot.
    Without this, the first inference after idle takes ~10s (observed) vs ~100ms warm."""
    global _keepalive_thread
    if _keepalive_thread is not None and _keepalive_thread.is_alive():
        return
    if KEEPALIVE_SECS <= 0:
        return

    def _loop():
        # Short speech-like burst (500ms) — forces whisper's CUDA kernels to compile/autotune
        # NOW rather than on the first user utterance. Without this, cold-start is ~9s.
        warm_pcm = bytearray()
        period = 32
        half = period // 2
        n = SAMPLE_RATE * 500 // 1000
        for i in range(n):
            v = 12000 if (i % period) < half else -12000
            warm_pcm += v.to_bytes(2, "little", signed=True)
        warm_wav = _pcm_to_wav(bytes(warm_pcm))
        # Fire first warm-up ASAP (no initial delay) so the first real utterance is fast.
        first = True
        while not _stop_event.is_set():
            try:
                import transcription_service
                _t0 = time.time()
                transcription_service.transcribe_audio_bytes(
                    warm_wav,
                    content_type="audio/wav",
                    filename="keepalive.wav",
                    vad_filter=False,
                )
                elapsed = (time.time() - _t0) * 1000
                if first:
                    logger.info("whisper warm-up done (%.0fms)", elapsed)
                    first = False
                else:
                    logger.debug("whisper keepalive ping ok (%.0fms)", elapsed)
            except Exception:
                logger.exception("whisper keepalive ping failed (non-fatal)")
            if _stop_event.wait(KEEPALIVE_SECS):
                return

    _keepalive_thread = threading.Thread(
        target=_loop, daemon=True, name="whisper-keepalive"
    )
    _keepalive_thread.start()
    logger.info("whisper keepalive thread started (interval=%ds)", KEEPALIVE_SECS)


def stop_all(timeout: float = 5.0) -> None:
    _stop_event.set()
    source_quality.stop_feedback_consumer()
    for state in list(_states.values()):
        try:
            state.queue.put_nowait(None)
        except Exception:
            pass
    deadline = time.time() + timeout
    for state in list(_states.values()):
        remaining = max(0.0, deadline - time.time())
        state.thread.join(timeout=remaining)
    _states.clear()


def status() -> list[dict]:
    return [
        {
            "source": s.source_id,
            "qsize": s.queue.qsize(),
            "dropped": s.dropped,
            "submitted": s.submitted,
            "alive": s.thread.is_alive(),
            "source_quality": source_quality.snapshot(s.source_id),
        }
        for s in _states.values()
    ]
