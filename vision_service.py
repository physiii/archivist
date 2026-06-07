"""Vision service — YOLOv8 object detection + CLIP embeddings on keyframes.

One YOLO model and one CLIP model, each semaphore-gated. Both run on the main
video stream's keyframes only (never decode non-keyframes). CLIP is throttled
per-source to ~1 embed per CLIP_EMBED_INTERVAL_S so we don't drown Milvus.

CLIP vectors + keyframe thumbnails land in Milvus collection `clip_embeddings`
(created on first use). Text search goes through /api/media/search?q=...
"""

from __future__ import annotations

import io
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any, Deque, Optional

import numpy as np

import events_bus
from sources_config import Source

logger = logging.getLogger("archivist.vision")

YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov8s.pt")
YOLO_GPU_ID = int(os.getenv("YOLO_GPU_ID", "0"))
YOLO_MAX_CONCURRENT = max(1, int(os.getenv("YOLO_MAX_CONCURRENT", "1")))
YOLO_IMG_SIZE = int(os.getenv("YOLO_IMG_SIZE", "320"))
YOLO_DEFAULT_CONF = float(os.getenv("YOLO_DEFAULT_CONF", "0.5"))
VISION_HISTORY_S = float(os.getenv("VISION_HISTORY_S", "600"))
VISION_QUEUE_MAX = int(os.getenv("VISION_QUEUE_MAX", "64"))
VISION_WORKERS = max(1, int(os.getenv("VISION_WORKERS", "1")))

CLIP_ENABLED = (os.getenv("CLIP_ENABLED") or "true").strip().lower() in ("1", "true", "yes", "on")
CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "ViT-B-32")
CLIP_MODEL_PRETRAINED = os.getenv("CLIP_MODEL_PRETRAINED", "laion2b_s34b_b79k")
CLIP_GPU_ID = int(os.getenv("CLIP_GPU_ID", "0"))
CLIP_MAX_CONCURRENT = max(1, int(os.getenv("CLIP_MAX_CONCURRENT", "1")))
CLIP_EMBED_INTERVAL_S = float(os.getenv("CLIP_EMBED_INTERVAL_S", "5"))
CLIP_THUMB_WIDTH = int(os.getenv("CLIP_THUMB_WIDTH", "640"))

KEYFRAMES_ROOT = Path(os.getenv("ARCHIVIST_KEYFRAMES_ROOT", "/data/media_store/keyframes"))
MILVUS_HOST = os.getenv("MILVUS_HOST", "host.docker.internal")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
CLIP_COLLECTION = os.getenv("CLIP_COLLECTION", "clip_embeddings")

# Frigate's tracked classes + per-class filters.
CLASS_FILTERS = {
    "person": {"conf": 0.7, "min_area": 1000, "max_area": 100000},
    "car":    {"conf": 0.7, "min_area": 2000, "max_area": None},
    "truck":  {"conf": 0.7, "min_area": 2000, "max_area": None},
}

_yolo_model = None
_yolo_lock = threading.Lock()
_yolo_sem = threading.Semaphore(YOLO_MAX_CONCURRENT)

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None
_clip_dim: Optional[int] = None
_clip_lock = threading.Lock()
_clip_sem = threading.Semaphore(CLIP_MAX_CONCURRENT)

_milvus_alias: Optional[str] = None
_milvus_collection = None
_milvus_lock = threading.Lock()

_available = False
_clip_available = False
_init_error: Optional[str] = None


@dataclass
class _SourceState:
    source_id: str
    frames_seen: int = 0
    detections_published: int = 0
    embeddings_published: int = 0
    last_embed_wall: float = 0.0
    recent: Deque[dict] = field(default_factory=lambda: deque(maxlen=1024))


_states: dict[str, _SourceState] = {}
_states_lock = threading.Lock()


@dataclass(frozen=True)
class _VisionJob:
    source: Source
    frame: np.ndarray
    wall_ts: float
    segment_path: Optional[str]


_vision_queue: Queue = Queue(maxsize=VISION_QUEUE_MAX)
_vision_threads: list[threading.Thread] = []
_vision_queue_lock = threading.Lock()
_vision_dropped = 0


_yolo_device: str = "cpu"

_CUDA_ERROR_MARKERS = (
    "out of memory", "unspecified launch failure", "launch failure",
    "illegal memory access", "device-side assert", "cublas", "cudnn",
    "cuda error", "cuda runtime error", "cuda driver",
)


def _is_cuda_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _CUDA_ERROR_MARKERS)


def _handle_yolo_cuda_failure(exc: Exception) -> None:
    global _yolo_device
    logger.error("YOLO CUDA failure — marking vision degraded: %s", exc)
    _yolo_device = "cpu"
    try:
        import notifications as _notif
        _notif.send_all(
            "YOLO GPU failure — vision degraded",
            f"YOLO inference hit a CUDA error and cannot continue on GPU.\n"
            f"Error: {exc}\n"
            f"Vision will attempt CPU fallback on next frame.",
            severity="error",
        )
    except Exception:
        logger.debug("YOLO GPU failure notification failed", exc_info=True)


def _init_yolo() -> None:
    global _yolo_model, _available, _init_error, _yolo_device
    if _yolo_model is not None:
        return
    with _yolo_lock:
        if _yolo_model is not None:
            return
        try:
            from ultralytics import YOLO
            import torch
            device = f"cuda:{YOLO_GPU_ID}" if torch.cuda.is_available() else "cpu"
            logger.info("loading YOLO model=%s device=%s", YOLO_MODEL_NAME, device)
            m = YOLO(YOLO_MODEL_NAME)
            dummy = np.zeros((YOLO_IMG_SIZE, YOLO_IMG_SIZE, 3), dtype=np.uint8)
            _ = m.predict(source=dummy, imgsz=YOLO_IMG_SIZE, device=device, verbose=False)
            _yolo_model = m
            _yolo_device = device
            _available = True
            _init_error = None
            logger.info("YOLO ready (classes=%d, device=%s)", len(m.names), device)
        except Exception as exc:
            _init_error = str(exc)
            _available = False
            logger.exception("YOLO init failed: %s", exc)


def _init_clip() -> None:
    global _clip_model, _clip_preprocess, _clip_tokenizer, _clip_dim, _clip_available
    if not CLIP_ENABLED or _clip_model is not None:
        return
    with _clip_lock:
        if _clip_model is not None:
            return
        try:
            import torch
            import open_clip
            device = f"cuda:{CLIP_GPU_ID}" if torch.cuda.is_available() else "cpu"
            logger.info("loading CLIP model=%s pretrained=%s device=%s",
                        CLIP_MODEL_NAME, CLIP_MODEL_PRETRAINED, device)
            model, _, preprocess = open_clip.create_model_and_transforms(
                CLIP_MODEL_NAME,
                pretrained=CLIP_MODEL_PRETRAINED,
                device=device,
            )
            model.eval()
            tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
            # Warm-up
            with torch.no_grad():
                probe_img = torch.zeros(1, 3, 224, 224, device=device)
                probe_feat = model.encode_image(probe_img)
                _clip_dim = int(probe_feat.shape[-1])
            _clip_model = model
            _clip_preprocess = preprocess
            _clip_tokenizer = tokenizer
            _clip_available = True
            logger.info("CLIP ready (dim=%d)", _clip_dim)
        except Exception as exc:
            logger.exception("CLIP init failed: %s", exc)
            _clip_available = False


def _milvus_collection_handle():
    """Get or lazily-create the Milvus collection for CLIP vectors."""
    global _milvus_alias, _milvus_collection
    if _milvus_collection is not None:
        return _milvus_collection
    with _milvus_lock:
        if _milvus_collection is not None:
            return _milvus_collection
        try:
            from pymilvus import (
                connections, utility, Collection, CollectionSchema, FieldSchema, DataType,
            )
            alias = f"clip_{MILVUS_HOST}_{MILVUS_PORT}".replace(".", "_")
            try:
                utility.list_collections(using=alias, timeout=3.0)
            except Exception:
                connections.connect(alias, host=MILVUS_HOST, port=MILVUS_PORT, timeout=3.0)
            if utility.has_collection(CLIP_COLLECTION, using=alias):
                col = Collection(CLIP_COLLECTION, using=alias)
            else:
                if _clip_dim is None:
                    _init_clip()
                dim = _clip_dim or 512
                schema = CollectionSchema(
                    fields=[
                        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=64),
                        FieldSchema(name="wall_ts", dtype=DataType.DOUBLE),
                        FieldSchema(name="keyframe_path", dtype=DataType.VARCHAR, max_length=512),
                        FieldSchema(name="segment_path", dtype=DataType.VARCHAR, max_length=512),
                        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
                    ],
                    description="CLIP embeddings of camera keyframes",
                )
                col = Collection(CLIP_COLLECTION, schema=schema, using=alias)
                col.create_index(
                    field_name="vector",
                    index_params={
                        "index_type": "HNSW",
                        "metric_type": "COSINE",
                        "params": {"M": 16, "efConstruction": 200},
                    },
                )
                logger.info("created Milvus collection %s (dim=%d, HNSW/COSINE)", CLIP_COLLECTION, dim)
            try:
                col.load()
            except Exception:
                pass
            _milvus_alias = alias
            _milvus_collection = col
            return col
        except Exception:
            logger.exception("Milvus init failed for collection %s", CLIP_COLLECTION)
            return None


def is_available() -> bool:
    return _available


def clip_available() -> bool:
    return _clip_available


def _ensure_state(source_id: str) -> _SourceState:
    with _states_lock:
        s = _states.get(source_id)
        if s is None:
            s = _SourceState(source_id=source_id)
            _states[source_id] = s
        return s


def _prune_recent(state: _SourceState, now: float) -> None:
    cutoff = now - VISION_HISTORY_S
    while state.recent and state.recent[0]["wall_ts"] < cutoff:
        state.recent.popleft()


def _point_in_polygon(px: float, py: float, polygon_px: list[tuple[float, float]]) -> bool:
    n = len(polygon_px)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_px[i]
        xj, yj = polygon_px[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _zones_for_bbox(source: Source, bbox: tuple[int, int, int, int], frame_w: int, frame_h: int) -> list[str]:
    if not source.zones:
        return []
    x, y, w, h = bbox
    cx = x + w / 2.0
    cy = y + h / 2.0
    hits: list[str] = []
    for name, flat in source.zones.items():
        if not flat or len(flat) < 6 or len(flat) % 2 != 0:
            continue
        pts = [(float(flat[i]) * frame_w, float(flat[i + 1]) * frame_h)
               for i in range(0, len(flat), 2)]
        if _point_in_polygon(cx, cy, pts):
            hits.append(name)
    return hits


def _save_thumbnail(source_id: str, frame_bgr: np.ndarray, wall_ts: float) -> Optional[str]:
    try:
        import cv2
        from datetime import datetime, timezone
        now = datetime.fromtimestamp(wall_ts, tz=timezone.utc)
        day_dir = KEYFRAMES_ROOT / source_id / now.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        ts_name = now.strftime("%H%M%S") + f"_{int(now.microsecond / 1000):03d}"
        path = day_dir / f"{ts_name}.jpg"
        h, w = frame_bgr.shape[:2]
        if w > CLIP_THUMB_WIDTH:
            scale = CLIP_THUMB_WIDTH / w
            frame_bgr = cv2.resize(frame_bgr, (CLIP_THUMB_WIDTH, int(h * scale)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(path), frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        return str(path)
    except Exception:
        logger.exception("thumbnail save failed for %s", source_id)
        return None


def _clip_embed_image(frame_bgr: np.ndarray) -> Optional[np.ndarray]:
    if _clip_model is None:
        return None
    try:
        import torch
        from PIL import Image
        rgb = frame_bgr[:, :, ::-1]
        img = Image.fromarray(rgb)
        dev = next(_clip_model.parameters()).device
        with _clip_sem:
            with torch.no_grad():
                tensor = _clip_preprocess(img).unsqueeze(0).to(dev)
                feat = _clip_model.encode_image(tensor)
                feat = feat / feat.norm(dim=-1, keepdim=True)
                vec = feat[0].detach().cpu().numpy().astype(np.float32)
        return vec
    except Exception:
        logger.exception("CLIP image embed failed")
        return None


def clip_embed_text(query: str) -> Optional[np.ndarray]:
    if not CLIP_ENABLED:
        return None
    _init_clip()
    if _clip_model is None or _clip_tokenizer is None:
        return None
    try:
        import torch
        dev = next(_clip_model.parameters()).device
        with _clip_sem:
            with torch.no_grad():
                tokens = _clip_tokenizer([query]).to(dev)
                feat = _clip_model.encode_text(tokens)
                feat = feat / feat.norm(dim=-1, keepdim=True)
                vec = feat[0].detach().cpu().numpy().astype(np.float32)
        return vec
    except Exception:
        logger.exception("CLIP text embed failed")
        return None


def _run_clip_if_due(source: Source, frame_bgr: np.ndarray, wall_ts: float, segment_path: Optional[str]) -> None:
    if not CLIP_ENABLED:
        return
    state = _ensure_state(source.id)
    if (wall_ts - state.last_embed_wall) < CLIP_EMBED_INTERVAL_S:
        return
    if _clip_model is None:
        _init_clip()
        if _clip_model is None:
            return
    vec = _clip_embed_image(frame_bgr)
    if vec is None:
        return
    kf_path = _save_thumbnail(source.id, frame_bgr, wall_ts)
    if kf_path is None:
        return
    col = _milvus_collection_handle()
    vec_id: Optional[int] = None
    if col is not None:
        try:
            res = col.insert([
                [source.id],
                [float(wall_ts)],
                [kf_path],
                [segment_path or ""],
                [vec.tolist()],
            ])
            pks = getattr(res, "primary_keys", None) or []
            if pks:
                vec_id = int(pks[0])
        except Exception:
            logger.exception("Milvus insert failed for %s", source.id)
    state.last_embed_wall = wall_ts
    state.embeddings_published += 1
    events_bus.publish(
        "clip.embedding", source.id,
        {"keyframe_path": kf_path, "segment_path": segment_path, "vector_id": vec_id,
         "frame_wh": [int(frame_bgr.shape[1]), int(frame_bgr.shape[0])]},
        wall_ts=wall_ts,
    )


def process_frame(
    source: Source,
    frame: np.ndarray,
    wall_ts: Optional[float] = None,
    segment_path: Optional[str] = None,
) -> list[dict]:
    """Run YOLO (+CLIP when due) on one BGR frame. Returns list of published detections."""
    if frame is None or frame.size == 0:
        return []
    if not _available:
        _init_yolo()
    if _yolo_model is None:
        return []
    if wall_ts is None:
        wall_ts = time.time()

    h, w = frame.shape[:2]
    state = _ensure_state(source.id)
    state.frames_seen += 1

    acquired = _yolo_sem.acquire(timeout=0.5)
    if not acquired:
        return []
    inference_s = 0.0
    results = []
    try:
        t0 = time.time()
        results = _yolo_model.predict(
            source=frame, imgsz=YOLO_IMG_SIZE, conf=YOLO_DEFAULT_CONF,
            device=_yolo_device, verbose=False,
        )
        inference_s = time.time() - t0
    except Exception as exc:
        if _is_cuda_error(exc) and _yolo_device.startswith("cuda"):
            _handle_yolo_cuda_failure(exc)
        else:
            logger.exception("YOLO inference failed for %s", source.id)
    finally:
        _yolo_sem.release()

    published: list[dict] = []
    if results:
        res = results[0]
        names = res.names
        try:
            boxes = res.boxes
            if boxes is not None:
                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                cls_ids = boxes.cls.cpu().numpy().astype(int)
                for i in range(len(xyxy)):
                    cls_name = names.get(int(cls_ids[i]), "unknown")
                    filt = CLASS_FILTERS.get(cls_name)
                    if filt is None:
                        continue
                    conf = float(confs[i])
                    if conf < filt["conf"]:
                        continue
                    x1, y1, x2, y2 = xyxy[i].tolist()
                    bw = int(max(0, x2 - x1))
                    bh = int(max(0, y2 - y1))
                    area = bw * bh
                    if area < filt["min_area"]:
                        continue
                    if filt.get("max_area") and area > filt["max_area"]:
                        continue
                    bbox = (int(x1), int(y1), bw, bh)
                    zones = _zones_for_bbox(source, bbox, w, h)
                    event = {
                        "class": cls_name,
                        "confidence": round(conf, 4),
                        "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
                        "area": area,
                        "zones": zones,
                        "frame_wh": [w, h],
                        "inference_s": round(inference_s, 4),
                    }
                    state.recent.append({"wall_ts": wall_ts, **event})
                    state.detections_published += 1
                    events_bus.publish("detection.object", source.id, event, wall_ts=wall_ts)
                    published.append(event)
        except Exception:
            logger.exception("YOLO result unpack failed for %s", source.id)

    _prune_recent(state, wall_ts)

    # CLIP embed (throttled per source). Runs after YOLO so detections are ready.
    try:
        _run_clip_if_due(source, frame, wall_ts, segment_path)
    except Exception:
        logger.exception("CLIP embed path failed for %s", source.id)

    return published


def _vision_worker_loop(worker_id: int) -> None:
    while True:
        try:
            job = _vision_queue.get(timeout=1.0)
        except Empty:
            continue
        try:
            process_frame(
                job.source,
                job.frame,
                wall_ts=job.wall_ts,
                segment_path=job.segment_path,
            )
        except Exception:
            logger.exception("async vision worker %d failed for %s", worker_id, job.source.id)
        finally:
            _vision_queue.task_done()


def _ensure_vision_workers() -> None:
    with _vision_queue_lock:
        while len(_vision_threads) < VISION_WORKERS:
            worker_id = len(_vision_threads) + 1
            t = threading.Thread(
                target=_vision_worker_loop,
                args=(worker_id,),
                daemon=True,
                name=f"vision-worker-{worker_id}",
            )
            _vision_threads.append(t)
            t.start()
            logger.info("started async vision worker %d", worker_id)


def enqueue_frame(
    source: Source,
    frame: np.ndarray,
    wall_ts: Optional[float] = None,
    segment_path: Optional[str] = None,
) -> bool:
    """Queue a keyframe for vision work without blocking RTSP ingest."""
    global _vision_dropped
    if frame is None or frame.size == 0:
        return False
    _ensure_vision_workers()
    job = _VisionJob(
        source=source,
        frame=frame.copy(),
        wall_ts=time.time() if wall_ts is None else float(wall_ts),
        segment_path=segment_path,
    )
    try:
        _vision_queue.put_nowait(job)
        return True
    except Full:
        try:
            _vision_queue.get_nowait()
            _vision_queue.task_done()
            _vision_dropped += 1
        except Empty:
            pass
        try:
            _vision_queue.put_nowait(job)
            return True
        except Full:
            _vision_dropped += 1
            if _vision_dropped <= 5 or _vision_dropped % 50 == 0:
                logger.warning(
                    "dropping vision keyframe for %s: queue full (size=%d dropped=%d)",
                    source.id,
                    _vision_queue.qsize(),
                    _vision_dropped,
                )
            return False


def search_by_text(query: str, top_k: int = 10, sources: Optional[list[str]] = None) -> list[dict]:
    """Encode text with CLIP, search Milvus collection, return top-k results."""
    vec = clip_embed_text(query)
    if vec is None:
        return []
    col = _milvus_collection_handle()
    if col is None:
        return []
    try:
        expr = None
        if sources:
            quoted = ", ".join(f'"{s}"' for s in sources)
            expr = f"source in [{quoted}]"
        res = col.search(
            data=[vec.tolist()],
            anns_field="vector",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=max(1, int(top_k)),
            expr=expr,
            output_fields=["source", "wall_ts", "keyframe_path", "segment_path"],
        )
    except Exception:
        logger.exception("Milvus search failed")
        return []
    out = []
    if res and res[0]:
        for hit in res[0]:
            fields = getattr(hit, "fields", {}) or {}
            out.append({
                "id": int(getattr(hit, "id", 0) or 0),
                "score": float(getattr(hit, "score", 0.0)),
                "source": fields.get("source"),
                "wall_ts": fields.get("wall_ts"),
                "keyframe_path": fields.get("keyframe_path"),
                "segment_path": fields.get("segment_path"),
            })
    return out


def events_between(source_id: str, start_wall_ts: float, end_wall_ts: float) -> list[dict]:
    with _states_lock:
        s = _states.get(source_id)
        if s is None:
            return []
        return [
            {k: v for k, v in e.items() if k != "wall_ts"} | {"wall_ts": e["wall_ts"]}
            for e in s.recent
            if start_wall_ts <= e["wall_ts"] <= end_wall_ts
        ]


def status() -> list[dict]:
    with _states_lock:
        per_source = [
            {
                "source": s.source_id,
                "frames_seen": s.frames_seen,
                "detections": s.detections_published,
                "embeddings": s.embeddings_published,
                "recent_size": len(s.recent),
            }
            for s in _states.values()
        ]
    return per_source + [{
        "yolo_available": _available,
        "clip_available": _clip_available,
        "clip_dim": _clip_dim,
        "init_error": _init_error,
        "queue_size": _vision_queue.qsize(),
        "queue_max": VISION_QUEUE_MAX,
        "queue_dropped": _vision_dropped,
        "workers": len(_vision_threads),
    }]


def start() -> None:
    """Initialize YOLO + CLIP eagerly. Safe to call once at boot."""
    _ensure_vision_workers()
    _init_yolo()
    if CLIP_ENABLED:
        _init_clip()
        _milvus_collection_handle()
