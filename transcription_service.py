"""Transcription service for Archivist.

Runs faster-whisper inside Archivist as the primary backend and keeps an
optional remote backend available only when explicitly configured. The public
response shape is compatible with the legacy TranscribeServer API.
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import subprocess
import struct
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import requests

logger = logging.getLogger("archivist.transcription")

# ── Configuration ────────────────────────────────────────────────────────

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


TRANSCRIBE_MODEL = (os.getenv("TRANSCRIBE_MODEL") or "medium.en").strip()
COMPUTE_TYPE = (os.getenv("TRANSCRIBE_COMPUTE_TYPE") or "float16").strip()
BEAM_SIZE = max(1, _env_int("TRANSCRIBE_BEAM_SIZE", 1))
TEMPERATURE = float(os.getenv("TRANSCRIBE_TEMPERATURE", "0.0"))
CONDITION_ON_PREVIOUS_TEXT = (os.getenv("TRANSCRIBE_CONDITION_ON_PREVIOUS_TEXT") or "false").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
GPU_INDEX = max(0, _env_int("TRANSCRIBE_GPU_ID", 0))
# 0 (or unset) = unbounded: let concurrency be limited by the real producers
# (one worker thread per source + media/API callers) and GPU capacity, not an
# arbitrary number. Set a positive value only as a safety valve if the GPU OOMs.
MAX_CONCURRENT = _env_int("TRANSCRIBE_MAX_CONCURRENT", 0)
# ctranslate2 serializes inference through num_workers (default 1). This is the
# real parallelism lever — it lets that many transcriptions run concurrently on
# the GPU. Removing MAX_CONCURRENT alone does nothing without this.
NUM_WORKERS = max(1, _env_int("TRANSCRIBE_NUM_WORKERS", 4))
TARGET_PEAK = float(os.getenv("TRANSCRIBE_TARGET_PEAK", "0.10"))
MAX_GAIN = float(os.getenv("TRANSCRIBE_MAX_GAIN", "15.0"))
FALLBACK_NO_SPEECH_THRESHOLD = float(os.getenv("TRANSCRIBE_FALLBACK_NO_SPEECH_THRESHOLD", "0.30"))
TRANSCRIBE_PROVIDER = (os.getenv("TRANSCRIBE_PROVIDER") or "local_first").strip().lower()
TRANSCRIBE_API_URL = (os.getenv("TRANSCRIBE_API_URL") or "").strip().rstrip("/")
TRANSCRIBE_API_TIMEOUT_S = max(30, int(os.getenv("TRANSCRIBE_API_TIMEOUT_S", "1800")))
PRELOAD_LOCAL_MODEL = (os.getenv("TRANSCRIBE_PRELOAD_LOCAL") or "false").strip().lower() in ("1", "true", "yes", "on")
LOCAL_TRANSCRIBE_MODEL = (os.getenv("TRANSCRIBE_LOCAL_MODEL") or "").strip()
REQUIRE_CUDA = (os.getenv("TRANSCRIBE_REQUIRE_CUDA") or "false").strip().lower() in ("1", "true", "yes", "on")

# ── Module state ─────────────────────────────────────────────────────────

_model = None
_model_lock = threading.Lock()
_transcribe_lock = threading.Semaphore(MAX_CONCURRENT) if MAX_CONCURRENT > 0 else contextlib.nullcontext()
_available = False
_init_error: str | None = None
_local_available = False
_local_error: str | None = None
_remote_available = False
_remote_error: str | None = None
_local_attempted = False
_remote_attempted = False
_local_device = "not_loaded"
_local_device_index: int | None = None
_local_compute_type: str | None = None


def is_available() -> bool:
    return _available


def get_status() -> dict:
    device = "not_loaded"
    if _local_available:
        device = _local_device or "unknown"
    elif _remote_available:
        device = "remote"
    cuda_status = _cuda_runtime_status(
        _local_device_index if _local_device == "cuda" else GPU_INDEX
    )
    return {
        "available": _available,
        "provider": TRANSCRIBE_PROVIDER,
        "remote_url": TRANSCRIBE_API_URL,
        "model": TRANSCRIBE_MODEL,
        "local_model": _resolve_local_model_name(TRANSCRIBE_MODEL),
        "compute_type": COMPUTE_TYPE,
        "local_compute_type": _local_compute_type,
        "beam_size": BEAM_SIZE,
        "temperature": TEMPERATURE,
        "condition_on_previous_text": CONDITION_ON_PREVIOUS_TEXT,
        "device": device,
        "device_index": _local_device_index,
        "gpu": {
            "requested_device_index": GPU_INDEX,
            "resolved_device_index": _local_device_index,
            "nvidia_visible_devices": os.getenv("NVIDIA_VISIBLE_DEVICES"),
            "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
            **cuda_status,
        },
        "backends": {
            "remote": {
                "available": _remote_available,
                "error": _remote_error,
            },
            "local": {
                "available": _local_available,
                "error": _local_error,
            },
        },
        "error": _init_error,
    }


def _has_cuda() -> bool:
    status = _cuda_runtime_status()
    return bool(status.get("available")) and int(status.get("device_count") or 0) > 0


def _cuda_runtime_status(selected_index: int | None = None) -> dict:
    status = {
        "available": False,
        "device_count": 0,
        "selected_device_index": selected_index,
        "selected_device_name": None,
        "device_names": [],
        "error": None,
    }
    try:
        import torch
    except Exception as exc:
        status["error"] = f"{type(exc).__name__}: {exc}"
        return status

    try:
        available = bool(torch.cuda.is_available())
        status["available"] = available
        if not available:
            return status
        count = int(torch.cuda.device_count())
        status["device_count"] = count
        names = []
        for idx in range(count):
            try:
                names.append(torch.cuda.get_device_name(idx))
            except Exception:
                names.append(f"cuda:{idx}")
        status["device_names"] = names
        if selected_index is not None and 0 <= selected_index < count:
            status["selected_device_name"] = names[selected_index]
    except Exception as exc:
        status["available"] = False
        status["error"] = f"{type(exc).__name__}: {exc}"
    return status


def _resolve_cuda_device_index(requested_index: int, cuda_status: dict) -> int:
    count = int(cuda_status.get("device_count") or 0)
    if count <= 0:
        return 0
    if 0 <= requested_index < count:
        return requested_index
    if count == 1:
        logger.warning(
            "TRANSCRIBE_GPU_ID=%d is outside the visible CUDA range; using cuda:0 "
            "inside the container. NVIDIA_VISIBLE_DEVICES=%s",
            requested_index,
            os.getenv("NVIDIA_VISIBLE_DEVICES"),
        )
        return 0
    raise RuntimeError(f"TRANSCRIBE_GPU_ID={requested_index} but only {count} CUDA devices are visible")


def _is_recoverable_cuda_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        marker in msg
        for marker in (
            "out of memory",
            "unspecified launch failure",
            "launch failure",
            "illegal memory access",
            "device-side assert",
            "cublas",
            "cudnn",
        )
    )


def _refresh_availability():
    global _available, _init_error
    _available = _remote_available or _local_available
    if _available:
        _init_error = None
        return
    errors = []
    if _remote_error:
        errors.append(f"remote: {_remote_error}")
    if _local_error:
        errors.append(f"local: {_local_error}")
    _init_error = "; ".join(errors) if errors else "no transcription backend available"


def _provider_allows_remote() -> bool:
    return TRANSCRIBE_PROVIDER in {"remote_only", "remote_first", "local_first"} and bool(TRANSCRIBE_API_URL)


def _provider_allows_local() -> bool:
    return TRANSCRIBE_PROVIDER in {"local_only", "local_first", "remote_first"}


def _probe_remote_service(force: bool = False) -> bool:
    global _remote_available, _remote_error, _remote_attempted
    if _remote_attempted and not force:
        return _remote_available
    _remote_attempted = True
    if not _provider_allows_remote():
        _remote_available = False
        _remote_error = "disabled by provider or missing TRANSCRIBE_API_URL"
        _refresh_availability()
        return False
    try:
        response = requests.get(
            f"{TRANSCRIBE_API_URL}/openapi.json",
            timeout=(5, 10),
        )
        response.raise_for_status()
        _remote_available = True
        _remote_error = None
    except Exception as exc:
        _remote_available = False
        _remote_error = str(exc)
    _refresh_availability()
    return _remote_available


def _canonical_whisper_model_name(model_name: str) -> str:
    normalized = (model_name or "").strip()
    if not normalized:
        return "medium.en"
    alias_map = {
        "medium-en": "medium.en",
        "medium_en": "medium.en",
        "turbo": "large-v3",
        "whisper-1": "large-v3",
    }
    return alias_map.get(normalized, normalized)


def _resolve_local_model_name(requested_model: str) -> str:
    if LOCAL_TRANSCRIBE_MODEL:
        return _canonical_whisper_model_name(LOCAL_TRANSCRIBE_MODEL)
    return _canonical_whisper_model_name(requested_model)


def _init_local_model():
    """Load the local faster-whisper model when local fallback is needed."""
    global _model, _local_available, _local_error, _local_attempted, _local_device, _local_device_index, _local_compute_type
    with _model_lock:
        if _model is not None:
            _local_available = True
            _local_error = None
            _refresh_availability()
            return
        if not _provider_allows_local():
            _local_available = False
            _local_error = "disabled by provider"
            _refresh_availability()
            return
        _local_attempted = True
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            _local_available = False
            _local_error = "faster-whisper not installed"
            logger.warning("Local transcription unavailable: faster-whisper not installed")
            _refresh_availability()
            return

        local_model = _resolve_local_model_name(TRANSCRIBE_MODEL)
        device = "cpu"
        compute = "int8"
        device_index = 0

        cuda_status = _cuda_runtime_status(GPU_INDEX)
        if cuda_status.get("available") and int(cuda_status.get("device_count") or 0) > 0:
            import torch
            try:
                device_index = _resolve_cuda_device_index(GPU_INDEX, cuda_status)
                torch.cuda.set_device(device_index)
                device = "cuda"
                compute = COMPUTE_TYPE
                logger.info(
                    "Loading Whisper model '%s' on cuda:%d (compute=%s, visible=%s)",
                    local_model,
                    device_index,
                    compute,
                    os.getenv("NVIDIA_VISIBLE_DEVICES"),
                )
            except Exception as exc:
                if REQUIRE_CUDA:
                    _local_available = False
                    _local_error = f"TRANSCRIBE_REQUIRE_CUDA=true but CUDA was visible yet unusable: {exc}"
                    _local_device = "error"
                    _local_device_index = None
                    _local_compute_type = None
                    logger.error("Whisper CUDA unusable and REQUIRE_CUDA=true; refusing CPU fallback: %s", exc)
                    _refresh_availability()
                    return
                logger.warning("CUDA was visible but unusable for Whisper; loading CPU int8 instead: %s", exc)
        else:
            if REQUIRE_CUDA:
                err = (
                    f"TRANSCRIBE_REQUIRE_CUDA=true but no CUDA devices visible "
                    f"(NVIDIA_VISIBLE_DEVICES={os.getenv('NVIDIA_VISIBLE_DEVICES')!r}, "
                    f"error={cuda_status.get('error')!r}). Whisper refuses CPU fallback."
                )
                _local_available = False
                _local_error = err
                _local_device = "error"
                _local_device_index = None
                _local_compute_type = None
                logger.error(err)
                _refresh_availability()
                return
            logger.warning(
                "CUDA not available for Whisper, loading '%s' on CPU (compute=int8; visible=%s; error=%s). "
                "Set TRANSCRIBE_REQUIRE_CUDA=true to forbid this fallback.",
                local_model,
                os.getenv("NVIDIA_VISIBLE_DEVICES"),
                cuda_status.get("error"),
            )

        if local_model != TRANSCRIBE_MODEL:
            logger.info(
                "Using local fallback model '%s' for remote model alias '%s'",
                local_model,
                TRANSCRIBE_MODEL,
            )

        try:
            try:
                _model = WhisperModel(
                    local_model,
                    device=device,
                    device_index=device_index,
                    compute_type=compute,
                    num_workers=NUM_WORKERS,
                )
            except Exception as exc:
                if device != "cuda" or not _is_recoverable_cuda_error(exc):
                    raise
                if REQUIRE_CUDA:
                    raise RuntimeError(
                        f"TRANSCRIBE_REQUIRE_CUDA=true and Whisper CUDA load failed; refusing CPU fallback: {exc}"
                    ) from exc
                logger.warning(
                    "Recoverable CUDA error while loading Whisper model; switching to CPU int8: %s",
                    exc,
                )
                device = "cpu"
                compute = "int8"
                device_index = 0
                _model = WhisperModel(
                    local_model,
                    device=device,
                    device_index=device_index,
                    compute_type=compute,
                    num_workers=NUM_WORKERS,
                )
            _local_available = True
            _local_error = None
            _local_device = device
            _local_device_index = device_index if device == "cuda" else None
            _local_compute_type = compute
            logger.info(
                "Local transcription model loaded successfully on %s%s (compute=%s)",
                device,
                f":{device_index}" if device == "cuda" else "",
                compute,
            )
        except Exception as exc:
            _local_available = False
            _local_error = str(exc)
            _local_device = "error"
            _local_device_index = None
            _local_compute_type = None
            logger.error("Failed to load local transcription model: %s", exc)
        _refresh_availability()


def _reload_local_model_on_cpu(exc: Exception):
    global _model, _local_available, _local_error, _local_device, _local_device_index, _local_compute_type
    if REQUIRE_CUDA:
        _local_available = False
        _local_error = (
            "TRANSCRIBE_REQUIRE_CUDA=true and Whisper CUDA inference failed; "
            f"refusing CPU fallback: {exc}"
        )
        _local_device = "error"
        _local_device_index = None
        _local_compute_type = None
        _refresh_availability()
        raise RuntimeError(_local_error) from exc

    from faster_whisper import WhisperModel

    local_model = _resolve_local_model_name(TRANSCRIBE_MODEL)
    with _model_lock:
        logger.warning(
            "Recoverable CUDA error during Whisper inference; switching transcription service to CPU int8: %s",
            exc,
        )
        _model = WhisperModel(
            local_model,
            device="cpu",
            device_index=0,
            compute_type="int8",
        )
        _local_available = True
        _local_error = None
        _local_device = "cpu"
        _local_device_index = None
        _local_compute_type = "int8"
        _refresh_availability()


def init_transcription_model():
    """Initialize remote and/or local transcription backends."""
    if _provider_allows_remote():
        _probe_remote_service(force=True)
    if (_provider_allows_local() and PRELOAD_LOCAL_MODEL) or (_provider_allows_local() and not _remote_available):
        _init_local_model()
    _refresh_availability()


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
        "temperature": TEMPERATURE,
        "condition_on_previous_text": CONDITION_ON_PREVIOUS_TEXT,
    }
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
    if no_speech_threshold is not None:
        kwargs["no_speech_threshold"] = no_speech_threshold
    if word_timestamps:
        kwargs["word_timestamps"] = True

    try:
        segments, info = _model.transcribe(audio, **kwargs)
        segments_list = list(segments)
    except Exception as exc:
        if not _is_recoverable_cuda_error(exc):
            raise
        _reload_local_model_on_cpu(exc)
        segments, info = _model.transcribe(audio, **kwargs)
        segments_list = list(segments)
    transcription = " ".join(seg.text for seg in segments_list).strip()
    audio_seconds = len(audio) / 16000.0 if len(audio) else 0.0
    no_speech_probs = []
    avg_logprobs = []
    compression_ratios = []
    for seg in segments_list:
        try:
            if getattr(seg, "no_speech_prob", None) is not None:
                no_speech_probs.append(float(getattr(seg, "no_speech_prob")))
        except Exception:
            pass
        try:
            if getattr(seg, "avg_logprob", None) is not None:
                avg_logprobs.append(float(getattr(seg, "avg_logprob")))
        except Exception:
            pass
        try:
            if getattr(seg, "compression_ratio", None) is not None:
                compression_ratios.append(float(getattr(seg, "compression_ratio")))
        except Exception:
            pass
    meta = {
        "pipeline": pipeline,
        "lang": info.language,
        "lang_p": info.language_probability,
        "audio_seconds": audio_seconds,
        "model_device": _local_device,
        "model_device_index": _local_device_index,
        "model_compute_type": _local_compute_type,
        "max_no_speech_prob": max(no_speech_probs) if no_speech_probs else None,
        "avg_logprob": (sum(avg_logprobs) / len(avg_logprobs)) if avg_logprobs else None,
        "max_compression_ratio": max(compression_ratios) if compression_ratios else None,
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

def _transcribe_audio_bytes_local(
    data: bytes,
    content_type: str = "",
    filename: str = "",
    initial_prompt: Optional[str] = None,
    no_speech_threshold: Optional[float] = None,
    vad_filter: bool = True,
    allow_fallback: bool = True,
    word_timestamps: bool = False,
) -> Tuple[str, dict, list]:
    """Transcribe audio bytes with the local faster-whisper model."""
    if _model is None:
        raise RuntimeError("Local transcription model not loaded")

    ctype = (content_type or "").lower()
    fname = (filename or "").lower()
    start = time.perf_counter()
    meta_extra = {"source_ctype": ctype, "source_fname": fname}

    with _transcribe_lock:
        # Raw PCM path
        if "audio/raw" in ctype or ("application/octet-stream" in ctype and fname.endswith(".raw")):
            audio = np.frombuffer(data, dtype=np.float32).astype(np.float32)
            audio_proc, proc_stats = _maybe_normalize_for_asr(audio)
            extra = {**meta_extra, "ffmpeg": False, "audio_stats": proc_stats, "vad_filter": bool(vad_filter)}
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
                extra = {
                    **meta_extra,
                    "channels": nch,
                    "chosen_channel": chosen_ch,
                    "ffmpeg": False,
                    "audio_stats": proc_stats,
                    "vad_filter": bool(vad_filter),
                }
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
                extra = {**meta_extra, "ffmpeg": True, "audio_stats": proc_stats, "vad_filter": bool(vad_filter)}
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
        extra = {**meta_extra, "ffmpeg": True, "audio_stats": proc_stats, "vad_filter": bool(vad_filter)}
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


def _remote_request_params(
    *,
    initial_prompt: Optional[str],
    no_speech_threshold: Optional[float],
    vad_filter: bool,
    allow_fallback: bool,
    word_timestamps: bool,
) -> dict:
    params = {
        "detailed": "true",
        "vad_filter": "true" if vad_filter else "false",
        "allow_fallback": "true" if allow_fallback else "false",
        "word_timestamps": "true" if word_timestamps else "false",
    }
    if initial_prompt:
        params["initial_prompt"] = initial_prompt
    if no_speech_threshold is not None:
        params["no_speech_threshold"] = str(no_speech_threshold)
    return params


def _parse_remote_response(payload: dict) -> Tuple[str, dict, list]:
    return (
        payload.get("transcription", "") or "",
        {
            "pipeline": payload.get("pipeline", "remote_api"),
            "lang": payload.get("language", "en"),
            "lang_p": payload.get("language_probability", 0.0),
            "audio_seconds": payload.get("audio_seconds", 0.0),
            "ffmpeg": payload.get("ffmpeg_used", False),
            "fallback": payload.get("fallback_used", False),
            "audio_stats": payload.get("audio_stats"),
            "max_no_speech_prob": payload.get("max_no_speech_prob", payload.get("no_speech_prob")),
            "avg_logprob": payload.get("avg_logprob"),
            "max_compression_ratio": payload.get("max_compression_ratio"),
            "process_time": payload.get("timing", {}).get("total", 0.0),
            "provider": "remote",
            "remote_url": TRANSCRIBE_API_URL,
        },
        payload.get("segments", []) or [],
    )


def _remote_transcribe_file(
    file_path: str,
    *,
    upload_name: str,
    content_type: str,
    initial_prompt: Optional[str],
    no_speech_threshold: Optional[float],
    vad_filter: bool,
    allow_fallback: bool,
    word_timestamps: bool,
) -> Tuple[str, dict, list]:
    params = _remote_request_params(
        initial_prompt=initial_prompt,
        no_speech_threshold=no_speech_threshold,
        vad_filter=vad_filter,
        allow_fallback=allow_fallback,
        word_timestamps=word_timestamps,
    )
    with open(file_path, "rb") as fh:
        response = requests.post(
            f"{TRANSCRIBE_API_URL}/",
            params=params,
            files={"file": (upload_name, fh, content_type)},
            timeout=(30, TRANSCRIBE_API_TIMEOUT_S),
        )
    response.raise_for_status()
    return _parse_remote_response(response.json())


def _remote_transcribe_audio_bytes(
    data: bytes,
    *,
    filename: str,
    content_type: str,
    initial_prompt: Optional[str],
    no_speech_threshold: Optional[float],
    vad_filter: bool,
    allow_fallback: bool,
    word_timestamps: bool,
) -> Tuple[str, dict, list]:
    suffix = Path(filename or "audio.bin").suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return _remote_transcribe_file(
            tmp_path,
            upload_name=filename or Path(tmp_path).name,
            content_type=content_type or "application/octet-stream",
            initial_prompt=initial_prompt,
            no_speech_threshold=no_speech_threshold,
            vad_filter=vad_filter,
            allow_fallback=allow_fallback,
            word_timestamps=word_timestamps,
        )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _extract_media_audio_to_wav(path: str) -> str:
    """Extract the first audio stream from a media file as 16 kHz mono WAV."""
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"Media file not found: {path}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
            "-vn", "-sn", "-dn",
            "-map", "0:a:0?",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            out_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=max(300, int(src.stat().st_size / (5 * 1024 * 1024))),
        )
        if result.returncode != 0 or not Path(out_path).exists() or Path(out_path).stat().st_size == 0:
            err = (result.stderr or b"").decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"ffmpeg audio extraction failed: {err[:400]}")
        return out_path
    except Exception:
        try:
            os.remove(out_path)
        except OSError:
            pass
        raise


def _select_backend() -> str:
    if TRANSCRIBE_PROVIDER == "remote_only":
        if not _remote_available:
            _probe_remote_service(force=True)
        if _remote_available:
            return "remote"
        raise RuntimeError(_remote_error or "Remote transcription backend unavailable")

    if TRANSCRIBE_PROVIDER == "local_only":
        if not _local_available:
            _init_local_model()
        if _local_available:
            return "local"
        raise RuntimeError(_local_error or "Local transcription backend unavailable")

    if TRANSCRIBE_PROVIDER == "local_first":
        if not _local_available:
            _init_local_model()
        if _local_available:
            return "local"
        if _provider_allows_remote() and (_remote_available or _probe_remote_service(force=True)):
            return "remote"
        raise RuntimeError(_local_error or _remote_error or "No transcription backend available")

    if _provider_allows_remote() and (_remote_available or _probe_remote_service(force=True)):
        return "remote"
    if _provider_allows_local():
        _init_local_model()
        if _local_available:
            return "local"
    raise RuntimeError(_remote_error or _local_error or "No transcription backend available")


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
    """Transcribe uploaded audio bytes using the configured backend."""
    if not _available:
        init_transcription_model()
    try:
        backend = _select_backend()
    except RuntimeError as exc:
        raise RuntimeError(f"Transcription service not available: {exc}") from exc
    if backend == "remote":
        try:
            return _remote_transcribe_audio_bytes(
                data,
                filename=filename,
                content_type=content_type,
                initial_prompt=initial_prompt,
                no_speech_threshold=no_speech_threshold,
                vad_filter=vad_filter,
                allow_fallback=allow_fallback,
                word_timestamps=word_timestamps,
            )
        except Exception as exc:
            logger.warning("Remote transcription failed: %s", exc)
            if TRANSCRIBE_PROVIDER == "remote_first" and _provider_allows_local():
                _init_local_model()
                if _local_available:
                    return _transcribe_audio_bytes_local(
                        data,
                        content_type=content_type,
                        filename=filename,
                        initial_prompt=initial_prompt,
                        no_speech_threshold=no_speech_threshold,
                        vad_filter=vad_filter,
                        allow_fallback=allow_fallback,
                        word_timestamps=word_timestamps,
                    )
            raise
    return _transcribe_audio_bytes_local(
        data,
        content_type=content_type,
        filename=filename,
        initial_prompt=initial_prompt,
        no_speech_threshold=no_speech_threshold,
        vad_filter=vad_filter,
        allow_fallback=allow_fallback,
        word_timestamps=word_timestamps,
    )


def transcribe_media_file(
    path: str,
    filename: str = "",
    initial_prompt: Optional[str] = None,
    no_speech_threshold: Optional[float] = None,
    vad_filter: bool = True,
    allow_fallback: bool = True,
    word_timestamps: bool = True,
) -> Tuple[str, dict, list]:
    """Transcribe a media file by extracting audio first instead of reading the whole file."""
    if not _available:
        init_transcription_model()
    try:
        backend = _select_backend()
    except RuntimeError as exc:
        raise RuntimeError(f"Transcription service not available: {exc}") from exc
    wav_path = _extract_media_audio_to_wav(path)
    try:
        if backend == "remote":
            try:
                return _remote_transcribe_file(
                    wav_path,
                    upload_name=(filename or Path(path).stem) + ".wav",
                    content_type="audio/wav",
                    initial_prompt=initial_prompt,
                    no_speech_threshold=no_speech_threshold,
                    vad_filter=vad_filter,
                    allow_fallback=allow_fallback,
                    word_timestamps=word_timestamps,
                )
            except Exception as exc:
                logger.warning("Remote media transcription failed: %s", exc)
                if TRANSCRIBE_PROVIDER == "remote_first" and _provider_allows_local():
                    _init_local_model()
                    if _local_available:
                        data = Path(wav_path).read_bytes()
                        return _transcribe_audio_bytes_local(
                            data,
                            content_type="audio/wav",
                            filename=(filename or Path(path).stem) + ".wav",
                            initial_prompt=initial_prompt,
                            no_speech_threshold=no_speech_threshold,
                            vad_filter=vad_filter,
                            allow_fallback=allow_fallback,
                            word_timestamps=word_timestamps,
                        )
                raise
        data = Path(wav_path).read_bytes()
        return _transcribe_audio_bytes_local(
            data,
            content_type="audio/wav",
            filename=(filename or Path(path).stem) + ".wav",
            initial_prompt=initial_prompt,
            no_speech_threshold=no_speech_threshold,
            vad_filter=vad_filter,
            allow_fallback=allow_fallback,
            word_timestamps=word_timestamps,
        )
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass


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
        "vad_filter": meta.get("vad_filter", True),
        "fallback_used": bool(meta.get("fallback", False)),
        "audio_stats": meta.get("audio_stats"),
        "max_no_speech_prob": meta.get("max_no_speech_prob"),
        "avg_logprob": meta.get("avg_logprob"),
        "max_compression_ratio": meta.get("max_compression_ratio"),
        "timing": {
            "total": meta.get("process_time", 0.0),
            "read": meta.get("read_time", 0.0),
            "wait": meta.get("wait_time", 0.0),
            "process": meta.get("process_time", 0.0),
            "model": meta.get("process_time", 0.0),
        },
    }

    segments_out = []
    for seg in segments:
        if isinstance(seg, dict):
            seg_obj = {
                "id": seg.get("id"),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", ""),
                "avg_logprob": seg.get("avg_logprob"),
                "no_speech_prob": seg.get("no_speech_prob"),
            }
            if word_timestamps and seg.get("words") is not None:
                seg_obj["words"] = seg.get("words")
            segments_out.append(seg_obj)
            continue
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
