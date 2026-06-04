"""Unit tests for motion_service — synthetic frames, mask application, debouncing."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def fresh_motion():
    import motion_service
    import events_bus

    # Reset module state between tests
    motion_service._states.clear()
    published = []

    def _fake_publish(topic, source, payload, **kw):
        published.append((topic, source, payload, kw))

    orig = events_bus.publish
    events_bus.publish = _fake_publish  # type: ignore
    yield motion_service, published
    events_bus.publish = orig  # type: ignore
    motion_service._states.clear()


def _make_source(src_id="cam", threshold=40, contour_area=100, mask=(), improve_contrast=False):
    import sources_config
    motion = sources_config.MotionProfile(
        threshold=threshold,
        contour_area=contour_area,
        improve_contrast=improve_contrast,
        mask=tuple(float(x) for x in mask),
    )
    return sources_config.Source(
        id=src_id,
        enabled=True,
        kind="camera",
        location=src_id,
        audio_url=None,
        video_main_url=None,
        video_sub_url=None,
        rtsp_transport="tcp",
        reconnect_min_s=2,
        reconnect_max_s=60,
        detect=sources_config.DetectProfile(),
        motion=motion,
    )


def _frame(w, h, fill=0, patch=None):
    """Return BGR frame; optionally paint a bright patch at patch=(x,y,w,h)."""
    arr = np.full((h, w, 3), fill, dtype=np.uint8)
    if patch is not None:
        x, y, pw, ph = patch
        arr[y:y + ph, x:x + pw] = 255
    return arr


def _settle(motion_service, src, n=25):
    """Feed n static frames so MOG2 learns the background."""
    for _ in range(n):
        motion_service.process_frame(src, _frame(320, 240, fill=30))


def test_detects_bright_patch_on_settled_background(fresh_motion, monkeypatch):
    try:
        import cv2  # noqa: F401
    except ImportError:
        pytest.skip("cv2 not installed on host")
    ms, published = fresh_motion
    monkeypatch.setattr(ms, "MOTION_COOLDOWN_MS", 0)  # MOG2 fires on first few frames during settle
    src = _make_source(contour_area=50)
    _settle(ms, src)

    # Introduce a big bright patch — clear motion
    ev = ms.process_frame(src, _frame(320, 240, fill=30, patch=(50, 50, 120, 120)))
    assert ev is not None
    assert ev["changed_area_pct"] > 1.0
    assert len(ev["regions"]) >= 1
    # Should also have been published
    assert any(t == "detection.motion" for t, _s, _p, _k in published)


def test_cooldown_suppresses_repeats(fresh_motion, monkeypatch):
    try:
        import cv2  # noqa: F401
    except ImportError:
        pytest.skip("cv2 not installed on host")
    import time
    ms, _ = fresh_motion
    monkeypatch.setattr(ms, "MOTION_COOLDOWN_MS", 0)
    src = _make_source(contour_area=50)
    _settle(ms, src)

    monkeypatch.setattr(ms, "MOTION_COOLDOWN_MS", 5000)
    # Jump far past any settle-time events so cooldown starts clean
    t0 = time.time() + 3600
    first = ms.process_frame(src, _frame(320, 240, fill=30, patch=(40, 40, 100, 100)), wall_ts=t0)
    assert first is not None
    # Same motion 1s later (< cooldown) — suppressed
    second = ms.process_frame(src, _frame(320, 240, fill=30, patch=(40, 40, 100, 100)), wall_ts=t0 + 1.0)
    assert second is None


def test_mask_excludes_ignored_region(fresh_motion, monkeypatch):
    try:
        import cv2  # noqa: F401
    except ImportError:
        pytest.skip("cv2 not installed on host")
    ms, _ = fresh_motion
    monkeypatch.setattr(ms, "MOTION_COOLDOWN_MS", 0)
    # Polygon covers the whole right half (0.5..1.0). Motion there should be ignored.
    src = _make_source(
        contour_area=50,
        mask=[0.5, 0.0, 1.0, 0.0, 1.0, 1.0, 0.5, 1.0],
    )
    _settle(ms, src)
    # Motion in right half (masked-out)
    ev = ms.process_frame(src, _frame(320, 240, fill=30, patch=(200, 50, 100, 100)))
    assert ev is None
    # Motion in left half (unmasked)
    ev = ms.process_frame(src, _frame(320, 240, fill=30, patch=(20, 50, 100, 100)))
    assert ev is not None


def test_events_between_returns_window(fresh_motion, monkeypatch):
    try:
        import cv2  # noqa: F401
    except ImportError:
        pytest.skip("cv2 not installed on host")
    ms, _ = fresh_motion
    monkeypatch.setattr(ms, "MOTION_COOLDOWN_MS", 0)
    src = _make_source(contour_area=50)
    _settle(ms, src)

    import time
    now = time.time()
    # Two events
    ms.process_frame(src, _frame(320, 240, fill=30, patch=(20, 20, 100, 100)), wall_ts=now + 1.0)
    ms.process_frame(src, _frame(320, 240, fill=30, patch=(60, 60, 100, 100)), wall_ts=now + 3.0)
    inside = ms.events_between(src.id, now + 0.5, now + 2.0)
    outside = ms.events_between(src.id, now + 10.0, now + 20.0)
    assert len(inside) == 1
    assert len(outside) == 0
