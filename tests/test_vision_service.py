"""Unit tests for vision_service — zone hit logic, class/confidence filter."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class _FakeBoxes:
    def __init__(self, xyxy, conf, cls):
        import types
        self.xyxy = types.SimpleNamespace(cpu=lambda: types.SimpleNamespace(numpy=lambda: np.array(xyxy, dtype=np.float32)))
        self.conf = types.SimpleNamespace(cpu=lambda: types.SimpleNamespace(numpy=lambda: np.array(conf, dtype=np.float32)))
        self.cls = types.SimpleNamespace(cpu=lambda: types.SimpleNamespace(numpy=lambda: np.array(cls, dtype=np.int64)))


class _FakeResult:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


class _FakeModel:
    def __init__(self, xyxy, conf, cls_ids, names):
        self._r = _FakeResult(_FakeBoxes(xyxy, conf, cls_ids), names)

    def predict(self, **kw):
        return [self._r]


@pytest.fixture
def patched_vision(monkeypatch):
    import vision_service as vs
    import events_bus
    vs._states.clear()

    published = []
    monkeypatch.setattr(events_bus, "publish",
                        lambda t, s, p, **k: published.append((t, s, p)))
    return vs, published


def _make_source(src_id="office", zones=None):
    import sources_config as sc
    return sc.Source(
        id=src_id, enabled=True, kind="camera", location=src_id,
        audio_url=None, video_main_url=None, video_sub_url=None,
        rtsp_transport="tcp", reconnect_min_s=2, reconnect_max_s=60,
        detect=sc.DetectProfile(),
        motion=None,
        zones=zones or {},
    )


def test_filters_to_tracked_classes_only(patched_vision, monkeypatch):
    vs, published = patched_vision
    # 3 detections: a person (tracked), a dog (ignored), a car (tracked)
    # YOLO COCO ids: 0=person, 16=dog, 2=car
    model = _FakeModel(
        xyxy=[[100, 100, 200, 300], [50, 50, 80, 90], [300, 300, 500, 450]],
        conf=[0.9, 0.95, 0.85],
        cls_ids=[0, 16, 2],
        names={0: "person", 16: "dog", 2: "car"},
    )
    monkeypatch.setattr(vs, "_yolo_model", model)
    monkeypatch.setattr(vs, "_available", True)
    monkeypatch.setattr(vs, "CLIP_ENABLED", False)

    src = _make_source()
    frame = np.zeros((480, 704, 3), dtype=np.uint8)
    detections = vs.process_frame(src, frame)
    classes = [d["class"] for d in detections]
    assert "person" in classes
    assert "car" in classes
    assert "dog" not in classes


def test_confidence_threshold_excludes_weak(patched_vision, monkeypatch):
    vs, published = patched_vision
    # person with conf 0.5 — below 0.7 threshold
    model = _FakeModel(
        xyxy=[[100, 100, 200, 300]],
        conf=[0.5],
        cls_ids=[0],
        names={0: "person"},
    )
    monkeypatch.setattr(vs, "_yolo_model", model)
    monkeypatch.setattr(vs, "CLIP_ENABLED", False)
    monkeypatch.setattr(vs, "_available", True)

    src = _make_source()
    frame = np.zeros((480, 704, 3), dtype=np.uint8)
    detections = vs.process_frame(src, frame)
    assert detections == []


def test_min_area_filter(patched_vision, monkeypatch):
    vs, published = patched_vision
    # Tiny bbox 10x10 = 100 px < 1000 min_area for person
    model = _FakeModel(
        xyxy=[[10, 10, 20, 20]],
        conf=[0.95],
        cls_ids=[0],
        names={0: "person"},
    )
    monkeypatch.setattr(vs, "_yolo_model", model)
    monkeypatch.setattr(vs, "CLIP_ENABLED", False)
    monkeypatch.setattr(vs, "_available", True)

    src = _make_source()
    detections = vs.process_frame(src, np.zeros((480, 704, 3), dtype=np.uint8))
    assert detections == []


def test_zone_hit_from_bbox_center(patched_vision, monkeypatch):
    vs, published = patched_vision
    # Zone: right-half rectangle (normalized). Person at center (150, 200) on 704x480 frame — left half, NOT in zone.
    zones = {
        "RightHalf": (0.5, 0.0, 1.0, 0.0, 1.0, 1.0, 0.5, 1.0),
    }
    # Person bbox centered at pixel (x=560, y=240) — well inside the right half
    model = _FakeModel(
        xyxy=[[500, 200, 620, 400]],
        conf=[0.95],
        cls_ids=[0],
        names={0: "person"},
    )
    monkeypatch.setattr(vs, "_yolo_model", model)
    monkeypatch.setattr(vs, "CLIP_ENABLED", False)
    monkeypatch.setattr(vs, "_available", True)

    src = _make_source(zones=zones)
    detections = vs.process_frame(src, np.zeros((480, 704, 3), dtype=np.uint8))
    assert len(detections) == 1
    assert "RightHalf" in detections[0]["zones"]


def test_events_between_window(patched_vision, monkeypatch):
    vs, _ = patched_vision
    model = _FakeModel(
        xyxy=[[100, 100, 200, 300]],
        conf=[0.9],
        cls_ids=[0],
        names={0: "person"},
    )
    monkeypatch.setattr(vs, "_yolo_model", model)
    monkeypatch.setattr(vs, "CLIP_ENABLED", False)
    monkeypatch.setattr(vs, "_available", True)

    src = _make_source()
    frame = np.zeros((480, 704, 3), dtype=np.uint8)
    import time as _time
    now = _time.time()
    vs.process_frame(src, frame, wall_ts=now + 1.0)
    vs.process_frame(src, frame, wall_ts=now + 3.0)
    inside = vs.events_between(src.id, now + 0.5, now + 2.0)
    outside = vs.events_between(src.id, now + 10.0, now + 20.0)
    assert len(inside) == 1
    assert len(outside) == 0
