from queue import Queue

import numpy as np


def _camera_source():
    from sources_config import DetectProfile, Source

    return Source(
        id="office",
        enabled=True,
        kind="camera",
        location="office",
        audio_url="rtsp://example/audio",
        video_main_url="rtsp://example/main",
        video_sub_url="rtsp://example/sub",
        rtsp_transport="tcp",
        reconnect_min_s=1.0,
        reconnect_max_s=2.0,
        detect=DetectProfile(),
        motion=None,
    )


def test_enqueue_frame_is_bounded_and_not_inline(monkeypatch):
    import vision_service as vision

    q = Queue(maxsize=1)
    calls = []
    monkeypatch.setattr(vision, "_vision_queue", q)
    monkeypatch.setattr(vision, "_vision_dropped", 0)
    monkeypatch.setattr(vision, "_ensure_vision_workers", lambda: None)
    monkeypatch.setattr(vision, "process_frame", lambda *args, **kwargs: calls.append((args, kwargs)))

    source = _camera_source()
    first = np.zeros((4, 4, 3), dtype=np.uint8)
    second = np.ones((4, 4, 3), dtype=np.uint8)

    assert vision.enqueue_frame(source, first, wall_ts=1.0, segment_path="/tmp/first.mp4")
    assert vision.enqueue_frame(source, second, wall_ts=2.0, segment_path="/tmp/second.mp4")

    assert calls == []
    assert vision._vision_dropped == 1
    job = q.get_nowait()
    assert job.wall_ts == 2.0
    assert job.segment_path == "/tmp/second.mp4"
    assert np.array_equal(job.frame, second)
