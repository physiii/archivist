"""Tests for the transcription service module."""

import io
import struct
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import transcription_service


# ── Audio helpers tests ─────────────────────────────────────────────────


def test_dbfs_zero():
    result = transcription_service._dbfs(0.0)
    assert result < -200  # Should be very negative


def test_dbfs_one():
    result = transcription_service._dbfs(1.0)
    assert result == pytest.approx(0.0, abs=0.01)


def test_dbfs_half():
    result = transcription_service._dbfs(0.5)
    assert result == pytest.approx(-6.02, abs=0.1)


def test_audio_stats_empty():
    audio = np.array([], dtype=np.float32)
    stats = transcription_service._audio_stats(audio)
    assert stats["samples"] == 0
    assert stats["rms"] == 0.0
    assert stats["peak"] == 0.0


def test_audio_stats_sine_wave():
    t = np.linspace(0, 1, 16000, dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    stats = transcription_service._audio_stats(audio)
    assert stats["samples"] == 16000
    assert stats["peak"] == pytest.approx(0.5, abs=0.01)
    assert stats["rms"] > 0.0
    assert stats["peak_dbfs"] == pytest.approx(-6.02, abs=0.5)


def test_maybe_normalize_normal_audio():
    """Normal volume audio should not be normalized."""
    audio = np.random.uniform(-0.3, 0.3, 16000).astype(np.float32)
    result, stats = transcription_service._maybe_normalize_for_asr(audio)
    assert stats["normalized"] is False
    assert stats["gain"] == 1.0
    np.testing.assert_array_equal(result, audio)


def test_maybe_normalize_quiet_audio():
    """Very quiet audio should be boosted."""
    audio = np.random.uniform(-0.001, 0.001, 16000).astype(np.float32)
    # Ensure it's non-silent
    audio[0] = 0.001
    result, stats = transcription_service._maybe_normalize_for_asr(audio)
    if stats.get("normalized"):
        assert stats["gain"] > 1.0
        assert np.max(np.abs(result)) > np.max(np.abs(audio))


def test_maybe_normalize_silent_audio():
    """Nearly silent audio should not be normalized."""
    audio = np.zeros(16000, dtype=np.float32)
    audio[0] = 1e-10  # Basically zero
    result, stats = transcription_service._maybe_normalize_for_asr(audio)
    assert stats["normalized"] is False


# ── WAV parsing tests ───────────────────────────────────────────────────


def _make_wav_bytes(sample_rate: int = 16000, duration_s: float = 0.1, channels: int = 1) -> bytes:
    """Generate a simple PCM16 WAV file in memory."""
    num_samples = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, num_samples * channels, dtype=np.float32)
    samples = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    buf = io.BytesIO()
    # fmt chunk
    fmt_data = struct.pack("<HHIIHH", 1, channels, sample_rate, sample_rate * channels * 2, channels * 2, 16)
    # data chunk
    data_bytes = samples.tobytes()

    # RIFF header
    total_size = 4 + (8 + len(fmt_data)) + (8 + len(data_bytes))
    buf.write(struct.pack("<4sI4s", b"RIFF", total_size, b"WAVE"))
    buf.write(struct.pack("<4sI", b"fmt ", len(fmt_data)))
    buf.write(fmt_data)
    buf.write(struct.pack("<4sI", b"data", len(data_bytes)))
    buf.write(data_bytes)
    return buf.getvalue()


def test_wav_bytes_to_float32_mono():
    wav_data = _make_wav_bytes(16000, 0.1, 1)
    audio, sr, nch, chosen = transcription_service._wav_bytes_to_float32(wav_data)
    assert sr == 16000
    assert nch == 1
    assert chosen is None
    assert len(audio) > 0
    assert audio.dtype == np.float32
    assert np.max(np.abs(audio)) <= 1.0


def test_wav_bytes_to_float32_stereo():
    wav_data = _make_wav_bytes(16000, 0.1, 2)
    audio, sr, nch, chosen = transcription_service._wav_bytes_to_float32(wav_data)
    assert sr == 16000
    assert nch == 2
    assert chosen is not None
    assert chosen in (0, 1)


def test_wav_bytes_invalid_header():
    with pytest.raises(RuntimeError, match="RIFF"):
        transcription_service._wav_bytes_to_float32(b"not a wav file at all")


def test_wav_bytes_incomplete():
    with pytest.raises(RuntimeError, match="Incomplete"):
        transcription_service._wav_bytes_to_float32(b"RIFF")


# ── Service state tests ─────────────────────────────────────────────────


def test_is_available_default():
    """Without init, service should not be available."""
    # Reset state
    transcription_service._model = None
    transcription_service._available = False
    transcription_service._local_available = False
    transcription_service._remote_available = False
    assert transcription_service.is_available() is False


def test_get_status_not_loaded():
    transcription_service._model = None
    transcription_service._available = False
    transcription_service._local_available = False
    transcription_service._remote_available = False
    transcription_service._init_error = None
    status = transcription_service.get_status()
    assert status["available"] is False
    assert status["device"] == "not_loaded"
    assert status["model"] == transcription_service.TRANSCRIBE_MODEL


def test_resolve_local_model_name_maps_turbo(monkeypatch):
    monkeypatch.setattr(transcription_service, "LOCAL_TRANSCRIBE_MODEL", "")
    assert transcription_service._resolve_local_model_name("turbo") == "large-v3"
    assert transcription_service._resolve_local_model_name("large-v3") == "large-v3"


def test_resolve_local_model_name_maps_medium_en_aliases(monkeypatch):
    monkeypatch.setattr(transcription_service, "LOCAL_TRANSCRIBE_MODEL", "")
    assert transcription_service._resolve_local_model_name("medium-en") == "medium.en"
    assert transcription_service._resolve_local_model_name("medium_en") == "medium.en"
    assert transcription_service._resolve_local_model_name("") == "medium.en"


def test_resolve_local_model_name_respects_override(monkeypatch):
    monkeypatch.setattr(transcription_service, "LOCAL_TRANSCRIBE_MODEL", "distil-large-v3")
    assert transcription_service._resolve_local_model_name("turbo") == "distil-large-v3"


def test_resolve_local_model_name_normalizes_override(monkeypatch):
    monkeypatch.setattr(transcription_service, "LOCAL_TRANSCRIBE_MODEL", "medium-en")
    assert transcription_service._resolve_local_model_name("turbo") == "medium.en"


def test_transcribe_when_unavailable(monkeypatch):
    """Should raise RuntimeError when service is not initialized."""
    transcription_service._model = None
    transcription_service._available = False
    transcription_service._local_available = False
    transcription_service._remote_available = False
    monkeypatch.setattr(transcription_service, "init_transcription_model", lambda: None)

    def raise_unavailable():
        raise RuntimeError("No transcription backend available")

    monkeypatch.setattr(transcription_service, "_select_backend", raise_unavailable)
    with pytest.raises(RuntimeError, match="not available"):
        transcription_service.transcribe_audio_bytes(b"fake audio data")


# ── Response builder tests ──────────────────────────────────────────────


def test_build_response_simple():
    response = transcription_service.build_transcribe_response("Hello world", {}, [])
    assert response == {"transcription": "Hello world"}


def test_build_response_detailed():
    meta = {
        "lang": "en",
        "lang_p": 0.99,
        "audio_seconds": 5.0,
        "pipeline": "wav_direct",
        "ffmpeg": False,
        "process_time": 0.5,
    }
    response = transcription_service.build_transcribe_response("Hello", meta, [], detailed=True)
    assert response["transcription"] == "Hello"
    assert response["language"] == "en"
    assert response["audio_seconds"] == 5.0
    assert "timing" in response
    assert "segments" in response


def test_build_response_with_mock_segments():
    seg = MagicMock()
    seg.id = 0
    seg.start = 0.0
    seg.end = 1.5
    seg.text = "Hello world"
    seg.avg_logprob = -0.1
    seg.no_speech_prob = 0.01
    seg.words = None

    response = transcription_service.build_transcribe_response(
        "Hello world", {"lang": "en", "lang_p": 0.99, "audio_seconds": 1.5, "pipeline": "test", "process_time": 0.1},
        [seg], detailed=True,
    )
    assert len(response["segments"]) == 1
    assert response["segments"][0]["text"] == "Hello world"
    assert response["segments"][0]["start"] == 0.0


def test_build_response_with_dict_segments():
    response = transcription_service.build_transcribe_response(
        "Hello world",
        {"lang": "en", "lang_p": 0.99, "audio_seconds": 1.5, "pipeline": "remote_api", "process_time": 0.1},
        [{"id": 1, "start": 0.0, "end": 1.5, "text": "Hello world", "words": [{"word": "Hello"}]}],
        detailed=True,
        word_timestamps=True,
    )
    assert len(response["segments"]) == 1
    assert response["segments"][0]["text"] == "Hello world"
    assert response["segments"][0]["words"][0]["word"] == "Hello"


def test_transcribe_audio_bytes_uses_remote_backend(monkeypatch):
    transcription_service._available = True
    monkeypatch.setattr(transcription_service, "_select_backend", lambda: "remote")
    monkeypatch.setattr(
        transcription_service,
        "_remote_transcribe_audio_bytes",
        lambda *args, **kwargs: ("hello", {"provider": "remote", "lang": "en"}, [{"text": "hello", "start": 0.0, "end": 1.0}]),
    )
    transcription, meta, segments = transcription_service.transcribe_audio_bytes(
        b"fake",
        content_type="audio/wav",
        filename="sample.wav",
        word_timestamps=True,
    )
    assert transcription == "hello"
    assert meta["provider"] == "remote"
    assert segments[0]["text"] == "hello"


def test_transcribe_media_file_uses_extracted_audio(monkeypatch, tmp_path):
    media_path = tmp_path / "sample.mkv"
    media_path.write_bytes(b"media")
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"wav")

    transcription_service._available = True
    monkeypatch.setattr(transcription_service, "_select_backend", lambda: "remote")
    monkeypatch.setattr(transcription_service, "_extract_media_audio_to_wav", lambda path: str(wav_path))

    seen = {}

    def fake_remote(path, **kwargs):
        seen["path"] = path
        seen["kwargs"] = kwargs
        return "hello", {"provider": "remote", "lang": "en"}, [{"text": "hello", "start": 0.0, "end": 1.0}]

    monkeypatch.setattr(transcription_service, "_remote_transcribe_file", fake_remote)
    transcription, meta, segments = transcription_service.transcribe_media_file(str(media_path))
    assert transcription == "hello"
    assert meta["provider"] == "remote"
    assert seen["path"] == str(wav_path)
    assert seen["kwargs"]["content_type"] == "audio/wav"
    assert seen["kwargs"]["upload_name"] == "sample.wav"
    assert segments[0]["text"] == "hello"
