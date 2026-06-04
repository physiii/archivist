"""Unit tests for streaming_transcription_service VAD segmenter.

We don't call whisper here — we synthesize int16 mono 16kHz PCM, alternate
silence with a simple buzz (all frames near max amplitude; webrtcvad is
energy-aware and treats this as speech-like), and check the segmenter
closes utterances correctly.
"""

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


SR = 16000


def _buzz_ms(ms: int) -> bytes:
    """Generate energetic buzz-like PCM that webrtcvad consistently classifies as speech."""
    n = SR * ms // 1000
    # Alternating max/min square wave at ~500Hz — high energy, mimics voiced audio envelope.
    period = 32  # ~500Hz at 16kHz
    half = period // 2
    frame = b""
    for i in range(n):
        v = 18000 if (i % period) < half else -18000
        frame += struct.pack("<h", v)
    return frame


def _silence_ms(ms: int) -> bytes:
    n = SR * ms // 1000
    return b"\x00\x00" * n


def test_segmenter_closes_utterance_on_hangover(monkeypatch):
    try:
        import webrtcvad  # noqa: F401
    except ImportError:
        pytest.skip("webrtcvad not installed in this environment")
    from streaming_transcription_service import _VadSegmenter

    seg = _VadSegmenter(aggressiveness=1)
    # 1000ms buzz → 700ms silence (> 600ms hangover) → should yield one utterance
    out = seg.feed(_buzz_ms(1000), stream_ts=0.0)
    assert out == []
    out = seg.feed(_silence_ms(800), stream_ts=1.0)
    assert len(out) == 1
    pcm, start, end = out[0]
    assert start is not None
    assert end is not None and end > start
    # Expect at least ~1s of PCM (may include some trailing silence)
    dur_ms = len(pcm) / (SR * 2) * 1000
    assert 900 <= dur_ms <= 1800


def test_segmenter_discards_short_utterance():
    try:
        import webrtcvad  # noqa: F401
    except ImportError:
        pytest.skip("webrtcvad not installed in this environment")
    from streaming_transcription_service import _VadSegmenter

    seg = _VadSegmenter(aggressiveness=1)
    # 200ms buzz → 800ms silence: shorter than MIN_UTTERANCE_MS (400), should discard
    seg.feed(_buzz_ms(200), stream_ts=0.0)
    out = seg.feed(_silence_ms(800), stream_ts=0.2)
    assert out == []


def test_pcm_to_wav_roundtrip():
    import wave
    import io
    from streaming_transcription_service import _pcm_to_wav

    pcm = _buzz_ms(100)
    wav = _pcm_to_wav(pcm)
    with wave.open(io.BytesIO(wav), "rb") as r:
        assert r.getnchannels() == 1
        assert r.getsampwidth() == 2
        assert r.getframerate() == SR
        assert r.readframes(r.getnframes()) == pcm


def test_transcribe_and_publish_uses_adaptive_profile(monkeypatch):
    import source_quality
    import streaming_transcription_service as streaming

    source_quality.reset_for_tests()
    source_quality.observe_audio("living_room", _silence_ms(300) + _buzz_ms(900) + _silence_ms(300))
    source_quality.observe_feedback("living_room", {"outcome": "hallucination_drop"})

    calls = []
    published = []

    class State:
        source_id = "living_room"
        submitted = 0

    class Segment:
        start = 0.0
        end = 1.0
        text = "turn off the lights"
        avg_logprob = -0.05
        no_speech_prob = 0.01
        compression_ratio = 1.0

    def fake_transcribe(wav, **kwargs):
        calls.append(kwargs)
        return (
            "turn off the lights",
            {"lang": "en", "max_no_speech_prob": 0.01, "avg_logprob": -0.05},
            [Segment()],
        )

    monkeypatch.setattr(streaming.events_bus, "publish", lambda topic, source, payload, **_kw: published.append((topic, source, payload)))

    streaming._transcribe_and_publish(State(), _buzz_ms(900), 0.0, 0.9, fake_transcribe)

    assert calls
    assert calls[0]["vad_filter"] is True
    assert calls[0]["allow_fallback"] is False
    assert calls[0]["no_speech_threshold"] >= 0.45
    assert published[-1][0] == "transcript.final"
    assert published[-1][2]["accepted_by_source_gate"] is True
    assert "source_quality" in published[-1][2]
