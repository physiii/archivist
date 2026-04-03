"""
Transcription service for Archivist.

Brings faster-whisper transcription directly into the archivist process,
replacing the need for a separate TranscribeServer container. Other services
can POST audio files to /api/transcribe and get the same response format.

GPU is used when available; falls back to CPU with a warning.
"""

from __future__ import annotations

import io
import logging
import os
import struct
import tempfile
import threading
import time
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger("archivist.transcription")

# ── Configuration ────────────────────────────────────────────────────────

TRANSCRIBE_MODEL = (os.getenv("TRANSCRIBE_MODEL") or "turbo").strip()
COMPUTE_TYPE = (os.getenv("TRANSCRIBE_COMPUTE_TYPE") or "float16").strip()
BEAM_SIZE = max(1, int(os.getenv("TRANSCRIBE_BEAM_SIZE", "1")))
GPU_INDEX = int(os.getenv("TRANSCRIBE_GPU_ID", "0"))
MAX_CONCURRENT = max(1, int(os.getenv("TRANSCRIBE_MAX_CONCURRENT", "1")))
TARGET_PEAK = float(os.getenv("TRANSCRIBE_TARGET_PEAK", "0.10"))
MAX_GAIN = float(os.getenv("TRANSCRIBE_MAX_GAIN", "15.0"))
FALLBACK_NO_SPEECH_THRESHOLD = float(os.getenv("TRANSCRIBE_FALLBACK_NO_SPEECH_THRESHOLD", "0.30"))

# ── Module state ─────────────────────────────────────────────────────────

_model = None
_model_lock = threading.Lock()
_transcribe_lock = threading.Semaphore(MAX_CONCURRENT)
_available = False
_init_error: str | None = None


def is_available() -> bool:
    return _available


def get_status() -> dict:
    return {
        "available": _available,
        "model": TRANSCRIBE_MODEL,
        "compute_type": COMPUTE_TYPE,
        "beam_size": BEAM_SIZE,
        "device": "cuda" if _available and _has_cuda() else "cpu" if _available else "not_loaded",
        "error": _init_error,
    }


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def init_transcription_model():
    """Load the faster-whisper model. Call at app startup."""
    global _model, _available, _init_error
    with _model_lock:
        if _model is not None:
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            _init_error = "faster-whisper not installed"
            logger.warning("Transcription unavailable: faster-whisper not installed")
            return

        device = "cpu"
        compute = "int8"
        device_index = 0

        if _has_cuda():
            import torch
            torch.cuda.set_device(GPU_INDEX)
            device = "cuda"
            compute = COMPUTE_TYPE
            device_index = GPU_INDEX
            logger.info("Loading Whisper model '%s' on cuda:%d (compute=%s)", TRANSCRIBE_MODEL, GPU_INDEX, compute)
        else:
            logger.info("CUDA not available, loading Whisper model '%s' on CPU (compute=int8)", TRANSCRIBE_MODEL)

        try:
            _model = WhisperModel(
                TRANSCRIBE_MODEL,
                device=device,
                device_index=device_index,
                compute_type=compute,
            )
            _available = True
            logger.info("Transcription model loaded successfully")
        except Exception as exc:
            _init_error = str(exc)
            logger.error("Failed to load transcription model: %s", exc)


# ── Audio helpers ────────────────────────────────────────────────────────

def _dbfs(x: float) -> float:
    return float(20.0 * np.log10(max(1e-12, x)))


def _audio_stats(audio: np.ndarray) -> dict:
    if audio.size == 0:
        return {"samples": 0, "rms": 0.0, "peak": 0.0, "rms_dbfs": -120.0, "peak_dbfs": -120.0}
    audio_f = audio.astype(np.float32, copy=False)
    peak = float(np.max(np.abs(audio_f)))
    rms = float(np.sqrt(np.mean(audio_f * audio_f)))
    return {
        "samples": int(audio_f.size),
        "rms": rms,
        "peak": peak,
        "rms_dbfs": _dbfs(rms),
        "peak_dbfs": _dbfs(peak),
    }


def _maybe_normalize_for_asr(audio: np.ndarray) -> Tuple[np.ndarray, dict]:
    stats = _audio_stats(audio)
    if stats["samples"] == 0:
        return audio, {**stats, "gain": 1.0, "normalized": False}
    peak = stats["peak"]
    rms_dbfs = stats["rms_dbfs"]
    peak_dbfs = stats["peak_dbfs"]
    non_silent = peak_dbfs > -60.0 and rms_dbfs > -75.0
    very_quiet = peak_dbfs < -35.0
    if not (non_silent and very_quiet):
        return audio, {**stats, "gain": 1.0, "normalized": False}
    gain = TARGET_PEAK / max(1e-12, peak)
    gain = min(gain, MAX_GAIN)
    boosted = np.clip(audio.astype(np.float32, copy=False) * gain, -1.0, 1.0).astype(np.float32)
    boosted_stats = _audio_stats(boosted)
    return boosted, {**boosted_stats, "gain": float(gain), "normalized": True}


def _wav_bytes_to_float32(data: bytes) -> Tuple[np.ndarray, int, int, Optional[int]]:
    """Parse WAV bytes and return (audio_float32_mono, sample_rate, n_channels, chosen_channel)."""
    bio = io.BytesIO(data)
    header = bio.read(12)
    if len(header) != 12:
        raise RuntimeError("Incomplete WAV header")
    riff, _filesize, wave_tag = struct.unpack("<4sI4s", header)
    if riff != b"RIFF" or wave_tag != b"WAVE":
        raise RuntimeError("Not a RIFF/WAVE file")

    fmt_chunk = None
    data_chunk = None
    while True:
        chunk_header = bio.read(8)
        if len(chunk_header) < 8:
            break
        chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)
        chunk_payload = bio.read(chunk_size)
        if len(chunk_payload) != chunk_size:
            raise RuntimeError("Truncated WAV chunk")
        if chunk_size % 2 == 1:
            bio.seek(1, io.SEEK_CUR)
        if chunk_id == b"fmt ":
            fmt_chunk = chunk_payload
        elif chunk_id == b"data":
            data_chunk = chunk_payload
        if fmt_chunk is not None and data_chunk is not None:
            break

    if fmt_chunk is None or data_chunk is None:
        raise RuntimeError("Missing fmt or data chunk in WAV")
    if len(fmt_chunk) < 16:
        raise RuntimeError("Invalid fmt chunk")

    audio_format, n_channels, sample_rate, _byte_rate, _block_align, bits_per_sample = struct.unpack(
        "<HHIIHH", fmt_chunk[:16]
    )

    if audio_format == 0xFFFE and len(fmt_chunk) >= 40:
        cb_size = struct.unpack("<H", fmt_chunk[16:18])[0]
        if cb_size >= 22:
            subformat = fmt_chunk[24:24 + 16]
            audio_format = struct.unpack("<H", subformat[:2])[0]

    if audio_format == 3:
        if bits_per_sample != 32:
            raise RuntimeError("Unsupported IEEE float width")
        arr = np.frombuffer(data_chunk, dtype="<f4")
    elif audio_format == 1:
        if bits_per_sample == 8:
            arr = np.frombuffer(data_chunk, dtype=np.uint8).astype(np.float32)
            arr = (arr - 128.0) / 128.0
        elif bits_per_sample == 16:
            arr = np.frombuffer(data_chunk, dtype="<i2").astype(np.float32) / 32768.0
        elif bits_per_sample == 32:
            arr = np.frombuffer(data_chunk, dtype="<i4").astype(np.float32) / 2147483648.0
        else:
            raise RuntimeError(f"Unsupported PCM bit depth: {bits_per_sample}")
    else:
        raise RuntimeError(f"Unsupported WAV audio format: {audio_format}")

    chosen_channel: Optional[int] = None
    if n_channels > 1:
        frames = arr.reshape(-1, n_channels)
        rms_per_ch = np.sqrt(np.mean(frames * frames, axis=0))
        chosen_channel = int(np.argmax(rms_per_ch))
        arr = frames[:, chosen_channel]

    return arr.astype(np.float32), sample_rate, n_channels, chosen_channel


def _run_ffmpeg_resample(orig_bytes: bytes) -> np.ndarray:
    """Convert arbitrary audio bytes to 16 kHz mono WAV via ffmpeg."""
    import ffmpeg as ffmpeg_lib
    with tempfile.NamedTemporaryFile(suffix=".in", delete=False) as f_in:
        f_in.write(orig_bytes)
        in_path = f_in.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_out:
        out_path = f_out.name
    try:
        ffmpeg_lib.input(in_path).output(out_path, ar=16000, ac=1, format="wav").overwrite_output().run(quiet=True)
        with open(out_path, "rb") as f:
            converted_bytes = f.read()
        arr, framerate, _, _ = _wav_bytes_to_float32(converted_bytes)
        if framerate != 16000:
            raise RuntimeError(f"ffmpeg resample failed, got sr={framerate}")
        return arr
    finally:
        for p in (in_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass


def _transcribe_audio_internal(
    audio: np.ndarray,
    pipeline: str,
    extra: dict,
    initial_prompt: Optional[str] = None,
    no_speech_threshold: Optional[float] = None,
    vad_filter: bool = True,
    word_timestamps: bool = False,
) -> Tuple[str, dict, list]:
    """Core transcription using the loaded model."""
    kwargs = {
        "language": "en",
        "beam_size": BEAM_SIZE,
        "vad_filter": bool(vad_filter),
    }
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
    if no_speech_threshold is not None:
        kwargs["no_speech_threshold"] = no_speech_threshold
    if word_timestamps:
        kwargs["word_timestamps"] = True

    segments, info = _model.transcribe(audio, **kwargs)
    segments_list = list(segments)
    transcription = " ".join(seg.text for seg in segments_list).strip()
    audio_seconds = len(audio) / 16000.0 if len(audio) else 0.0
    meta = {
        "pipeline": pipeline,
        "lang": info.language,
        "lang_p": info.language_probability,
        "audio_seconds": audio_seconds,
        **extra,
    }
    return transcription, meta, segments_list


def _try_with_vad_fallback(audio, pipeline, extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps, proc_stats):
    """Run transcription with optional VAD fallback on empty results."""
    transcription, meta, segments = _transcribe_audio_internal(
        audio, pipeline=pipeline, extra=extra,
        initial_prompt=initial_prompt, no_speech_threshold=no_speech_threshold,
        vad_filter=vad_filter, word_timestamps=word_timestamps,
    )
    if not transcription and vad_filter and proc_stats.get("peak_dbfs", -120.0) > -55.0:
        fallback_threshold = no_speech_threshold if no_speech_threshold is not None else FALLBACK_NO_SPEECH_THRESHOLD
        transcription, meta, segments = _transcribe_audio_internal(
            audio, pipeline=f"{pipeline}_vad_fallback",
            extra={**extra, "fallback": True},
            initial_prompt=initial_prompt, no_speech_threshold=fallback_threshold,
            vad_filter=False, word_timestamps=word_timestamps,
        )
    return transcription, meta, segments


# ── Public API ───────────────────────────────────────────────────────────

def transcribe_audio_bytes(
    data: bytes,
    content_type: str = "",
    filename: str = "",
    initial_prompt: Optional[str] = None,
    no_speech_threshold: Optional[float] = None,
    vad_filter: bool = True,
    allow_fallback: bool = True,
    word_timestamps: bool = False,
) -> Tuple[str, dict, list]:
    """
    Transcribe audio data. Returns (transcription_text, metadata, segments).

    This is the main entry point - matches the TranscribeServer API contract.
    Thread-safe via semaphore to prevent GPU thrashing.
    """
    if not _available or _model is None:
        raise RuntimeError("Transcription service not available")

    ctype = (content_type or "").lower()
    fname = (filename or "").lower()
    start = time.perf_counter()
    meta_extra = {"source_ctype": ctype, "source_fname": fname}

    with _transcribe_lock:
        # Raw PCM path
        if "audio/raw" in ctype or ("application/octet-stream" in ctype and fname.endswith(".raw")):
            audio = np.frombuffer(data, dtype=np.float32).astype(np.float32)
            audio_proc, proc_stats = _maybe_normalize_for_asr(audio)
            extra = {**meta_extra, "ffmpeg": False, "audio_stats": proc_stats}
            if allow_fallback:
                transcription, meta, segments = _try_with_vad_fallback(
                    audio_proc, "raw_pcm", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps, proc_stats
                )
            else:
                transcription, meta, segments = _transcribe_audio_internal(
                    audio_proc, "raw_pcm", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps
                )
            meta["process_time"] = time.perf_counter() - start
            return transcription, meta, segments

        # WAV path
        if "audio/wav" in ctype or fname.endswith(".wav"):
            try:
                audio, sr, nch, chosen_ch = _wav_bytes_to_float32(data)
            except Exception:
                audio, sr = None, None

            if audio is not None and sr == 16000:
                audio_proc, proc_stats = _maybe_normalize_for_asr(audio)
                extra = {**meta_extra, "channels": nch, "chosen_channel": chosen_ch, "ffmpeg": False, "audio_stats": proc_stats}
                if allow_fallback:
                    transcription, meta, segments = _try_with_vad_fallback(
                        audio_proc, "wav_direct", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps, proc_stats
                    )
                else:
                    transcription, meta, segments = _transcribe_audio_internal(
                        audio_proc, "wav_direct", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps
                    )
                meta["process_time"] = time.perf_counter() - start
                return transcription, meta, segments
            else:
                audio = _run_ffmpeg_resample(data)
                audio_proc, proc_stats = _maybe_normalize_for_asr(audio)
                extra = {**meta_extra, "ffmpeg": True, "audio_stats": proc_stats}
                if allow_fallback:
                    transcription, meta, segments = _try_with_vad_fallback(
                        audio_proc, "wav_ffmpeg", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps, proc_stats
                    )
                else:
                    transcription, meta, segments = _transcribe_audio_internal(
                        audio_proc, "wav_ffmpeg", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps
                    )
                meta["process_time"] = time.perf_counter() - start
                return transcription, meta, segments

        # Other formats (mp3, m4a, etc.) - ffmpeg resample
        audio = _run_ffmpeg_resample(data)
        audio_proc, proc_stats = _maybe_normalize_for_asr(audio)
        extra = {**meta_extra, "ffmpeg": True, "audio_stats": proc_stats}
        if allow_fallback:
            transcription, meta, segments = _try_with_vad_fallback(
                audio_proc, "other_ffmpeg", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps, proc_stats
            )
        else:
            transcription, meta, segments = _transcribe_audio_internal(
                audio_proc, "other_ffmpeg", extra, initial_prompt, no_speech_threshold, vad_filter, word_timestamps
            )
        meta["process_time"] = time.perf_counter() - start
        return transcription, meta, segments


def build_transcribe_response(transcription: str, meta: dict, segments: list, detailed: bool = False, word_timestamps: bool = False) -> dict:
    """Build the JSON response matching TranscribeServer's format."""
    if not detailed and not word_timestamps:
        return {"transcription": transcription}

    response = {
        "transcription": transcription,
        "language": meta.get("lang", "en"),
        "language_probability": meta.get("lang_p", 0.0),
        "audio_seconds": meta.get("audio_seconds", 0.0),
        "pipeline": meta.get("pipeline", "unknown"),
        "ffmpeg_used": meta.get("ffmpeg", False),
        "vad_filter": True,
        "fallback_used": bool(meta.get("fallback", False)),
        "audio_stats": meta.get("audio_stats"),
        "timing": {
            "total": meta.get("process_time", 0.0),
            "model": meta.get("process_time", 0.0),
        },
    }

    segments_out = []
    for seg in segments:
        seg_obj = {
            "id": getattr(seg, "id", None),
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "avg_logprob": getattr(seg, "avg_logprob", None),
            "no_speech_prob": getattr(seg, "no_speech_prob", None),
        }
        if word_timestamps and getattr(seg, "words", None) is not None:
            seg_obj["words"] = [
                {"start": w.start, "end": w.end, "word": w.word, "probability": getattr(w, "probability", None)}
                for w in seg.words
            ]
        segments_out.append(seg_obj)

    response["segments"] = segments_out
    return response
