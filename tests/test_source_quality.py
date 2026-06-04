import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import source_quality


SR = 16000


def _tone_ms(ms: int, amp: int = 9000) -> bytes:
    n = SR * ms // 1000
    out = bytearray()
    for i in range(n):
        sample = int(amp * math.sin(2.0 * math.pi * 440.0 * (i / SR)))
        out.extend(struct.pack("<h", sample))
    return bytes(out)


def _silence_ms(ms: int) -> bytes:
    return b"\x00\x00" * (SR * ms // 1000)


def test_audio_observation_derives_source_quality_profile():
    source_quality.reset_for_tests()

    pcm = _silence_ms(300) + _tone_ms(700) + _silence_ms(300)
    snapshot = source_quality.observe_audio("living_room", pcm, kind="mic", location="living_room")

    assert snapshot["source_id"] == "living_room"
    assert snapshot["quality_score"] > 0.0
    assert snapshot["snr_db"] is not None
    assert snapshot["vad_profile"]["allow_fallback"] is False


def test_low_quality_or_hallucination_feedback_tightens_vad_profile():
    source_quality.reset_for_tests()

    # Low dynamic range/noisy audio produces a stricter profile.
    pcm = _tone_ms(1200, amp=800)
    source_quality.observe_audio("living_room", pcm, kind="mic", location="living_room")
    before = source_quality.vad_profile("living_room")

    source_quality.observe_feedback("living_room", {"outcome": "hallucination_drop"})
    after = source_quality.vad_profile("living_room")

    assert after.allow_fallback is False
    assert after.aggressiveness >= before.aggressiveness
    assert after.min_utterance_ms >= before.min_utterance_ms
    assert after.no_speech_threshold >= before.no_speech_threshold


def test_transcript_decision_rejects_known_hallucination_pattern():
    source_quality.reset_for_tests()
    source_quality.observe_audio("living_room", _silence_ms(300) + _tone_ms(800) + _silence_ms(300))

    accepted, reason, snapshot = source_quality.transcript_decision(
        "living_room",
        "I'm going to go to the bathroom.",
        {"max_no_speech_prob": 0.01},
        [],
    )

    assert accepted is False
    assert reason == "hallucination_pattern"
    assert snapshot["hallucination_count"] == 1
