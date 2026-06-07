"""Ensure the RTSP ingest write path never decodes video packets.

The whole point of the segment writer is passthrough copy (no re-encode, no
decode). If someone accidentally calls packet.decode() on the video path,
this test catches it.
"""

import json
import os
import shutil
import subprocess
import sys
import time
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
    assert first_video.stream is v_in, "writer mutated the input packet stream"
    writer.close()
    container.close()


def test_segment_writer_rebases_nonzero_segment_timestamps(fixture_mp4, tmp_path, monkeypatch):
    """A segment that starts mid-stream should still start near timestamp zero."""
    try:
        import av
    except ImportError:
        pytest.skip("PyAV not installed")

    import rtsp_ingest_service as ingest
    monkeypatch.setattr(ingest, "SEGMENTS_ROOT", tmp_path / "segments")
    monkeypatch.setattr(ingest, "SEGMENT_TARGET_S", 60)
    monkeypatch.setattr(ingest.events_bus, "publish", lambda *a, **kw: None)

    container = av.open(str(fixture_mp4))
    v_in = container.streams.video[0]
    a_in = container.streams.audio[0]
    pkts = list(container.demux(v_in, a_in))
    keyframe_indexes = [
        idx for idx, packet in enumerate(pkts)
        if packet.stream.type == "video" and packet.is_keyframe and packet.dts is not None
    ]
    if len(keyframe_indexes) < 2:
        pytest.skip("fixture did not contain a second keyframe")

    writer = ingest._SegmentWriter("test_src", video_in_stream=v_in, audio_in_stream=a_in)
    for packet in pkts[keyframe_indexes[1]:]:
        writer.feed_packet(packet, is_video=packet.stream.type == "video")
    writer.close()
    container.close()

    segments = sorted((tmp_path / "segments" / "test_src").rglob("*.mp4"))
    assert segments
    with av.open(str(segments[0])) as out:
        video = out.streams.video[0]
        first_packet = next(packet for packet in out.demux(video) if packet.dts is not None)
        first_dts_s = float(first_packet.dts * first_packet.time_base)
    assert first_dts_s == pytest.approx(0.0, abs=0.1)


def test_segment_writer_sidecar_marks_stalled_capture(fixture_mp4, tmp_path, monkeypatch):
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
    for packet in container.demux(v_in, a_in):
        writer.feed_packet(packet, is_video=packet.stream.type == "video")
    container.close()

    assert writer._segment_start_wall is not None
    writer._segment_start_wall = time.time() - 60.0
    writer.close()

    sidecars = sorted((tmp_path / "segments" / "test_src").rglob("*.json"))
    assert sidecars
    sidecar = json.loads(sidecars[0].read_text())
    assert sidecar["capture_health"] == "stalled"
    assert sidecar["media_duration_s"] > 2.0
    assert sidecar["duration_s"] >= 59.0


def test_segment_writer_hard_cap_reopens_camera_only_on_keyframe(fixture_mp4, tmp_path, monkeypatch):
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
    pkts = list(container.demux(v_in, a_in))
    first_key = next(
        packet for packet in pkts
        if packet.stream.type == "video" and packet.is_keyframe and packet.dts is not None
    )
    audio_pkt = next(packet for packet in pkts if packet.stream.type == "audio" and packet.dts is not None)
    non_key = next(
        packet for packet in pkts
        if packet.stream.type == "video" and not packet.is_keyframe and packet.dts is not None
    )
    keyframes = [
        packet for packet in pkts
        if packet.stream.type == "video" and packet.is_keyframe and packet.dts is not None
    ]
    if len(keyframes) < 2:
        pytest.skip("fixture did not contain a second keyframe")

    writer = ingest._SegmentWriter("test_src", video_in_stream=v_in, audio_in_stream=a_in)
    writer.feed_packet(first_key, is_video=True)
    assert writer._container is not None

    assert writer._segment_start_wall is not None
    writer._segment_start_wall = time.time() - ingest.SEGMENT_MAX_S - 1.0
    writer.feed_packet(audio_pkt, is_video=False)
    assert writer._container is None, "hard-cap rotation reopened camera segment on audio"

    writer.feed_packet(non_key, is_video=True)
    assert writer._container is None, "hard-cap rotation reopened camera segment on a non-keyframe"

    writer.feed_packet(keyframes[1], is_video=True)
    assert writer._container is not None, "writer did not reopen on the next keyframe"
    writer.close()
    container.close()


def test_segment_writer_accepts_pts_only_packets(fixture_mp4, tmp_path, monkeypatch):
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
    first_key = next(
        packet for packet in container.demux(v_in, a_in)
        if packet.stream.type == "video" and packet.is_keyframe and packet.pts is not None
    )

    pts_only = av.Packet(bytes(first_key))
    pts_only.pts = first_key.pts
    pts_only.dts = None
    pts_only.time_base = first_key.time_base
    pts_only.is_keyframe = True
    pts_only.stream = v_in

    writer = ingest._SegmentWriter("test_src", video_in_stream=v_in, audio_in_stream=a_in)
    writer.feed_packet(pts_only, is_video=True)
    writer.close()
    container.close()

    sidecars = sorted((tmp_path / "segments" / "test_src").rglob("*.json"))
    assert sidecars
    sidecar = json.loads(sidecars[0].read_text())
    assert sidecar["packet_counts"]["video"] == 1
    assert sidecar["dropped_missing_timestamp_packets"] == 0


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


def test_camera_motion_detect_stream_is_opt_in(monkeypatch):
    import rtsp_ingest_service as ingest
    from sources_config import DetectProfile, Source

    source = Source(
        id="office",
        enabled=True,
        kind="camera",
        location="office",
        audio_url=None,
        video_main_url="rtsp://example/main",
        video_sub_url="rtsp://example/sub",
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=DetectProfile(fps=10),
        motion=None,
    )

    monkeypatch.setattr(ingest, "CAMERA_MOTION_ENABLED", False)
    assert ingest._should_start_detect_stream(source) is False

    monkeypatch.setattr(ingest, "CAMERA_MOTION_ENABLED", True)
    assert ingest._should_start_detect_stream(source) is True


def test_motion_frame_interval_respects_global_cap(monkeypatch):
    import rtsp_ingest_service as ingest
    from sources_config import DetectProfile, Source

    source = Source(
        id="office",
        enabled=True,
        kind="camera",
        location="office",
        audio_url=None,
        video_main_url="rtsp://example/main",
        video_sub_url="rtsp://example/sub",
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=DetectProfile(fps=10),
        motion=None,
    )

    monkeypatch.setattr(ingest, "CAMERA_MOTION_MAX_FPS", 2.0)

    assert ingest._motion_frame_interval_s(source) == pytest.approx(0.5)


def test_camera_main_stream_prefers_video_url_even_when_audio_url_is_set():
    import rtsp_ingest_service as ingest
    from sources_config import DetectProfile, Source

    source = Source(
        id="floodlight",
        enabled=True,
        kind="camera",
        location="floodlight",
        audio_url="rtsp://example/root",
        video_main_url="rtsp://example/h264Preview_01_sub",
        video_sub_url="rtsp://example/h264Preview_01_sub",
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=DetectProfile(fps=10),
        motion=None,
    )

    assert ingest._main_stream_url(source) == "rtsp://example/h264Preview_01_sub"


def test_configured_sources_status_is_inventory_without_urls(monkeypatch):
    import rtsp_ingest_service as ingest
    from sources_config import DetectProfile, MotionProfile, Source

    source = Source(
        id="office",
        enabled=True,
        kind="camera",
        location="office",
        audio_url="rtsp://user:password@example/main",
        video_main_url="rtsp://user:password@example/main",
        video_sub_url="rtsp://user:password@example/sub",
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=DetectProfile(fps=10),
        motion=MotionProfile(),
    )
    monkeypatch.setattr(ingest.sources_config, "enabled_sources", lambda: [source])

    status = ingest.configured_sources_status()

    assert status == [
        {
            "id": "office",
            "enabled": True,
            "kind": "camera",
            "location": "office",
            "has_audio": True,
            "has_video_main": True,
            "has_video_sub": True,
            "motion_enabled": True,
            "transcription_enabled": True,
            "segment_format": "mp4",
        }
    ]
    assert "rtsp://" not in json.dumps(status)
