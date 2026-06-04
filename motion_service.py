"""Motion detection for archivist's unified media pipeline.

Runs MOG2 background subtraction on decoded frames from each camera's detect
sub-stream (704x480 @ 10fps typically). CPU-only — cheap enough to run on
every frame. Emits detection.motion events when changed area crosses the
per-source threshold. Also maintains a short ring buffer of recent motion
events per source so segment close can stamp `labels: ["motion"]` on the
sidecar if any motion happened in the segment's wall-clock window.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Optional

import numpy as np

import events_bus
from sources_config import Source

logger = logging.getLogger("archivist.motion")

CONTOUR_MIN_AREA = int(os.getenv("MOTION_CONTOUR_MIN_AREA", "100"))
MOTION_COOLDOWN_MS = int(os.getenv("MOTION_COOLDOWN_MS", "500"))
MOTION_HISTORY_S = float(os.getenv("MOTION_HISTORY_S", "600"))  # keep last 10 min of events per source
MOG2_HISTORY = int(os.getenv("MOTION_MOG2_HISTORY", "500"))
MOG2_VAR_THRESHOLD = int(os.getenv("MOTION_MOG2_VAR_THRESHOLD", "16"))
MOG2_DETECT_SHADOWS = (os.getenv("MOTION_MOG2_DETECT_SHADOWS") or "false").strip().lower() in (
    "1", "true", "yes", "on"
)


@dataclass
class _SourceState:
    source_id: str
    width: int
    height: int
    threshold: int                  # per-source area threshold (from Frigate mask)
    contour_area: int               # min contour area in pixels
    improve_contrast: bool
    mask: Optional[np.ndarray] = None  # 2D uint8 (0/1), 1=count motion here
    bg: Any = None                      # cv2.BackgroundSubtractorMOG2 (untyped to avoid cv2 import)
    last_event_wall: float = 0.0
    recent: Deque[dict] = field(default_factory=lambda: deque(maxlen=1024))
    frames_seen: int = 0
    events_published: int = 0


_states: dict[str, _SourceState] = {}
_states_lock = threading.Lock()


def _build_mask(polygon_coords: tuple[float, ...], width: int, height: int):
    """Build a uint8 mask (1 inside polygon, 0 outside) from Frigate-style normalized polygon coords.

    Input is a flat list of alternating x,y normalized [0,1]. Frigate uses
    the mask to EXCLUDE regions (privacy/ignore zones), so we invert it:
    the returned mask has 1 where we SHOULD detect motion.
    """
    import cv2  # local import so tests can skip

    if not polygon_coords or len(polygon_coords) < 6 or len(polygon_coords) % 2 != 0:
        return None
    pts = np.array(
        [(float(polygon_coords[i]) * width, float(polygon_coords[i + 1]) * height)
         for i in range(0, len(polygon_coords), 2)],
        dtype=np.int32,
    )
    # Start with "detect everywhere", then carve out the ignore polygon.
    mask = np.ones((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 0)
    return mask


def _ensure_state(source: Source, width: int, height: int) -> _SourceState:
    import cv2

    with _states_lock:
        state = _states.get(source.id)
        if state is not None and (state.width == width and state.height == height):
            return state
        motion_profile = source.motion
        threshold = motion_profile.threshold if motion_profile else 40
        contour_area = max(CONTOUR_MIN_AREA, motion_profile.contour_area if motion_profile else 10)
        improve_contrast = motion_profile.improve_contrast if motion_profile else True
        mask = _build_mask(motion_profile.mask if motion_profile else (), width, height) if motion_profile else None
        bg = cv2.createBackgroundSubtractorMOG2(
            history=MOG2_HISTORY,
            varThreshold=MOG2_VAR_THRESHOLD,
            detectShadows=MOG2_DETECT_SHADOWS,
        )
        state = _SourceState(
            source_id=source.id,
            width=width,
            height=height,
            threshold=threshold,
            contour_area=contour_area,
            improve_contrast=improve_contrast,
            mask=mask,
            bg=bg,
        )
        _states[source.id] = state
        logger.info(
            "motion state initialized for %s (%dx%d thresh=%d contour_min=%d mask=%s)",
            source.id, width, height, threshold, contour_area, mask is not None,
        )
        return state


def _prune_recent(state: _SourceState, now: float) -> None:
    cutoff = now - MOTION_HISTORY_S
    while state.recent and state.recent[0]["wall_ts"] < cutoff:
        state.recent.popleft()


def process_frame(source: Source, frame: np.ndarray, wall_ts: Optional[float] = None) -> Optional[dict]:
    """Run MOG2 on one BGR or GRAY frame. Returns the event dict if motion fired, else None."""
    import cv2

    if frame is None or frame.size == 0:
        return None
    if wall_ts is None:
        wall_ts = time.time()
    if frame.ndim == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    h, w = gray.shape[:2]
    state = _ensure_state(source, w, h)
    state.frames_seen += 1

    if state.improve_contrast:
        gray = cv2.equalizeHist(gray)

    fg = state.bg.apply(gray)
    # MOG2 with shadows=True returns 127 for shadow, 255 for foreground. We treat >127 as motion.
    _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
    if state.mask is not None:
        fg = cv2.bitwise_and(fg, fg, mask=state.mask)

    # Find contours; a contour must exceed `threshold` AND min contour area.
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[list[int]] = []
    changed_px = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area < state.contour_area:
            continue
        x, y, rw, rh = cv2.boundingRect(c)
        regions.append([int(x), int(y), int(rw), int(rh)])
        changed_px += int(area)

    if not regions:
        return None

    frame_px = float(w * h) or 1.0
    changed_pct = 100.0 * changed_px / frame_px

    # Apply per-source threshold: interpret Frigate's `threshold` as MOG2 variance; we approximate
    # "enough motion" via changed pixel count > state.threshold (scaled to frame).
    # Threshold in Frigate is 0-255; here we gate via contour count/area already. Keep a minimum
    # changed_pct to avoid sensor-noise events.
    if changed_pct < 0.05:
        return None

    # Debounce: don't fire more than once per cooldown window.
    if (wall_ts - state.last_event_wall) * 1000.0 < MOTION_COOLDOWN_MS:
        return None
    state.last_event_wall = wall_ts

    event = {
        "changed_area_pct": round(changed_pct, 4),
        "changed_px": changed_px,
        "regions": regions[:16],  # cap for event size
        "n_regions": len(regions),
        "frame_wh": [w, h],
    }
    state.recent.append({"wall_ts": wall_ts, **event})
    _prune_recent(state, wall_ts)
    state.events_published += 1
    events_bus.publish("detection.motion", source.id, event, wall_ts=wall_ts)
    return event


def events_between(source_id: str, start_wall_ts: float, end_wall_ts: float) -> list[dict]:
    """Return motion events whose wall_ts lies within [start, end]. Used to stamp segment sidecars."""
    with _states_lock:
        state = _states.get(source_id)
        if state is None:
            return []
        return [
            {k: v for k, v in e.items() if k != "wall_ts"} | {"wall_ts": e["wall_ts"]}
            for e in state.recent
            if start_wall_ts <= e["wall_ts"] <= end_wall_ts
        ]


def status() -> list[dict]:
    with _states_lock:
        return [
            {
                "source": s.source_id,
                "width": s.width,
                "height": s.height,
                "frames_seen": s.frames_seen,
                "events_published": s.events_published,
                "recent_size": len(s.recent),
            }
            for s in _states.values()
        ]
