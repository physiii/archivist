import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_stalled_segment_marks_source_degraded(monkeypatch):
    import health_monitor

    health_monitor._sources.clear()
    monkeypatch.setattr(health_monitor, "HEALTH_SOURCE_STALE_S", 600.0)

    health_monitor.mark_event("source.health", "office", {"state": "up"})
    health_monitor.mark_event(
        "segment.written",
        "office",
        {
            "capture_health": "stalled",
            "path": "/data/media_store/segments/office/2026-06-07/010000.mp4",
            "duration_s": 60.0,
            "video_duration_s": 20.0,
            "video_packets_per_s": 3.0,
        },
    )

    status = health_monitor.status()

    assert status["status"] == "warning"
    assert status["sources"]["office"]["status"] == "degraded"
    assert status["sources"]["office"]["last_segment_health"] == "stalled"
    assert status["sources"]["office"]["last_segment_video_packets_per_s"] == 3.0
    assert status["sources"]["office"]["last_segment_video_duration_ratio"] == 0.333


def test_ok_segment_recovers_degraded_source(monkeypatch):
    import health_monitor

    health_monitor._sources.clear()
    monkeypatch.setattr(health_monitor, "HEALTH_SOURCE_STALE_S", 600.0)

    health_monitor.mark_event("source.health", "office", {"state": "up"})
    health_monitor.mark_event(
        "segment.written",
        "office",
        {"capture_health": "stalled", "duration_s": 60.0, "video_duration_s": 20.0},
    )
    assert health_monitor.status()["sources"]["office"]["status"] == "degraded"

    health_monitor.mark_event(
        "segment.written",
        "office",
        {"capture_health": "ok", "duration_s": 60.0, "video_duration_s": 60.0},
    )

    assert health_monitor.status()["sources"]["office"]["status"] == "healthy"
