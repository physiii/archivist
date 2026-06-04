"""Ensure the RTSP ingest write path never decodes video packets.

The whole point of the segment writer is passthrough copy (no re-encode, no
decode). If someone accidentally calls packet.decode() on the video path,
this test catches it.
"""

import os
import shutil
import subprocess
import sys
from array import array
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.fixture
def fixture_mp4(tmp_path):
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available on PATH")
    out = tmp_path / "fixture.mp4"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=black:size=320x240:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "3",
        "-c:v", "libx264", "-g", "15", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "16000", "-ac", "1",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    assert out.exists() and out.stat().st_size > 0
    return out


def test_segment_writer_never_decodes_video(fixture_mp4, tmp_path, monkeypatch):
    try:
        import av
    except ImportError:
        pytest.skip("PyAV not installed")

    import rtsp_ingest_service as ingest
    monkeypatch.setattr(ingest, "SEGMENTS_ROOT", tmp_path / "segments")
    monkeypatch.setattr(ingest, "SEGMENT_TARGET_S", 0.5)

    published: list[tuple] = []
    monkeypatch.setattr(
        ingest.events_bus, "publish",
        lambda topic, source, payload, **kw: published.append((topic, source, payload)),
    )

    container = av.open(str(fixture_mp4))
    v_in = container.streams.video[0]
    a_in = container.streams.audio[0]
    v_in_codec = v_in.codec_context.codec.name
    a_in_codec = a_in.codec_context.codec.name
    closed_count = 0

    def on_segment_closed():
        nonlocal closed_count
        closed_count += 1

    writer = ingest._SegmentWriter(
        "test_src",
        video_in_stream=v_in,
        audio_in_stream=a_in,
        on_segment_closed=on_segment_closed,
    )
    for packet in container.demux(v_in, a_in):
        writer.feed_packet(packet, is_video=packet.stream.type == "video")
    writer.close()
    container.close()

    # Behavioral assertion: passthrough preserves original codecs.
    segments = sorted((tmp_path / "segments" / "test_src").rglob("*.mp4"))
    assert len(segments) >= 1, "no segments written"
    for seg in segments:
        with av.open(str(seg)) as out:
            assert out.streams.video[0].codec_context.codec.name == v_in_codec, (
                f"video codec changed from {v_in_codec} to "
                f"{out.streams.video[0].codec_context.codec.name}; re-encode detected"
            )
            assert out.streams.audio[0].codec_context.codec.name == a_in_codec

    # Structural assertion: no .decode( references in the write path.
    src = Path(ingest.__file__).read_text()
    # Extract the _SegmentWriter class body.
    start = src.index("class _SegmentWriter")
    end = src.index("\ndef ", start)
    writer_src = src[start:end]
    assert "decode(" not in writer_src, "writer class contains a decode() call"

    topics = [t for t, _s, _p in published]
    assert "segment.written" in topics
    assert closed_count == topics.count("segment.written")


def test_segment_writer_waits_for_keyframe_to_open(fixture_mp4, tmp_path, monkeypatch):
    """Opening a camera segment on a non-keyframe would produce an unplayable file."""
    try:
        import av
    except ImportError:
        pytest.skip("PyAV not installed")

    import rtsp_ingest_service as ingest
    monkeypatch.setattr(ingest, "SEGMENTS_ROOT", tmp_path / "segments")
    monkeypatch.setattr(ingest.events_bus, "publish", lambda *a, **kw: None)

    container = av.open(str(fixture_mp4))
    v_in = container.streams.video[0]
    a_in = container.streams.audio[0]
    writer = ingest._SegmentWriter("test_src", video_in_stream=v_in, audio_in_stream=a_in)

    pkts = list(container.demux(v_in, a_in))
    # Find a non-keyframe video packet that appears before the first keyframe.
    first_video = next((p for p in pkts if p.stream.type == "video"), None)
    if first_video is None or not first_video.is_keyframe:
        pytest.skip("fixture didn't start with a keyframe as expected")

    # Feed only an audio packet first — writer should NOT open a segment yet.
    audio_pkt = next(p for p in pkts if p.stream.type == "audio")
    writer.feed_packet(audio_pkt, is_video=False)
    assert writer._container is None, "writer opened segment before seeing a video keyframe"

    writer.feed_packet(first_video, is_video=True)
    assert writer._container is not None, "writer didn't open on the first keyframe"
    writer.close()
    container.close()


def test_rtsp_errors_redact_credentials():
    import rtsp_ingest_service as ingest

    raw = "Invalid data found when processing input: 'rtsp://admin:secret@192.0.2.10:554/path'"
    redacted = ingest._safe_error(raw)

    assert "secret" not in redacted
    assert "admin:" not in redacted
    assert "rtsp://[redacted]" in redacted


def test_audio_level_stats_reports_int16_dbfs():
    import rtsp_ingest_service as ingest

    samples = array("h", [0, 1000, -1000, 0])
    stats = ingest._audio_level_stats(samples.tobytes())

    assert stats["audio_samples"] == 4
    assert stats["audio_peak"] == pytest.approx(1000 / 32768, abs=0.00001)
    assert stats["audio_peak_dbfs"] == pytest.approx(-30.3, abs=0.1)
    assert stats["audio_rms_dbfs"] == pytest.approx(-33.3, abs=0.1)


def test_audio_health_payload_marks_low_signal(monkeypatch):
    import rtsp_ingest_service as ingest
    from sources_config import Source

    monkeypatch.setattr(ingest, "AUDIO_LOW_RMS_DBFS", -70.0)
    source = Source(
        id="living_room",
        enabled=True,
        kind="mic",
        location="living_room",
        audio_url="rtsp://example/mic",
        video_main_url=None,
        video_sub_url=None,
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=ingest.sources_config.DetectProfile(),
        motion=None,
    )

    payload = ingest._audio_health_payload(source, b"\x00" * 640, None)

    assert payload["role"] == "audio"
    assert payload["audio_state"] == "low_signal"
    assert payload["voice_activity"] is False
    assert payload["audio_rms_dbfs"] == -120.0
