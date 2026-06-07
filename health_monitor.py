"""Health monitor — watchdog for the ingest pipeline.

Consumes source.health + segment.written events, runs freshness probes, and
dispatches notifications on state transitions (with cooldowns).

Public:
  start() / stop()                      — lifecycle
  status() -> dict                      — snapshot for /health endpoint
  mark_event(topic, source, payload)    — test-only entry

Design:
  - One bg consumer thread (events_bus.consume) for real-time state
  - One bg probe thread that ticks every HEALTH_PROBE_INTERVAL_S to detect
    silence (no events means nothing will fire)
  - Notifications are debounced: fire on healthy -> degraded transitions and
    again every HEALTH_REPEAT_S while still degraded; fire on recovery.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import events_bus
import notifications
import sources_config

logger = logging.getLogger("archivist.health")

HEALTH_SOURCE_STALE_S = float(os.getenv("HEALTH_SOURCE_STALE_S", "600"))   # 10 min
HEALTH_PROBE_INTERVAL_S = float(os.getenv("HEALTH_PROBE_INTERVAL_S", "60"))
HEALTH_REPEAT_S = float(os.getenv("HEALTH_REPEAT_S", "3600"))              # 1 h
HEALTH_STARTUP_GRACE_S = float(os.getenv("HEALTH_STARTUP_GRACE_S", "180")) # 3 min

_stop_event = threading.Event()
_consumer_thread: Optional[threading.Thread] = None
_probe_thread: Optional[threading.Thread] = None
_state_lock = threading.Lock()
_started_at: float = 0.0


@dataclass
class _SourceState:
    source_id: str
    last_event_wall_ts: float = 0.0
    last_health_state: str = "unknown"  # "up" | "down" | "connecting" | "unknown"
    last_error: Optional[str] = None
    status: str = "unknown"              # derived: "healthy" | "degraded" | "stale" | "down" | "unknown"
    first_bad_wall_ts: float = 0.0
    last_notified_wall_ts: float = 0.0
    last_segment_health: str = "unknown"
    last_segment_path: Optional[str] = None
    last_segment_written_ts: float = 0.0
    last_segment_video_packets_per_s: Optional[float] = None
    last_segment_video_duration_ratio: Optional[float] = None


_sources: dict[str, _SourceState] = {}


def _get_source_state(source_id: str) -> _SourceState:
    s = _sources.get(source_id)
    if s is None:
        s = _SourceState(source_id=source_id)
        _sources[source_id] = s
    return s


def mark_event(topic: str, source: str, payload: dict) -> None:
    """Apply one event to state. Called by the consumer and test code."""
    now = time.time()
    with _state_lock:
        s = _get_source_state(source)
        if topic == "segment.written":
            s.last_event_wall_ts = now
            s.last_segment_written_ts = now
            s.last_segment_health = str(payload.get("capture_health") or "unknown")
            s.last_segment_path = payload.get("path") or None
            try:
                s.last_segment_video_packets_per_s = float(payload["video_packets_per_s"])
            except Exception:
                s.last_segment_video_packets_per_s = None
            try:
                wall = float(payload.get("duration_s") or 0.0)
                video = float(payload.get("video_duration_s") or 0.0)
                s.last_segment_video_duration_ratio = (video / wall) if wall > 0 else None
            except Exception:
                s.last_segment_video_duration_ratio = None
        elif topic == "source.health":
            state = str(payload.get("state") or "unknown")
            s.last_health_state = state
            if state == "up":
                s.last_event_wall_ts = now
                s.last_error = None
            elif state in ("down", "reconnecting"):
                s.last_error = str(payload.get("error") or "")
        _recompute_status_locked(s, now)


def _recompute_status_locked(s: _SourceState, now: float) -> None:
    """Derive `status` from the most recent signals."""
    if s.last_health_state == "down":
        new_status = "down"
    elif s.last_health_state == "reconnecting":
        new_status = "degraded"
    elif s.last_event_wall_ts == 0.0:
        new_status = "unknown"
    elif (now - s.last_event_wall_ts) > HEALTH_SOURCE_STALE_S:
        new_status = "stale"
    elif s.last_segment_health not in ("ok", "unknown", ""):
        new_status = "degraded"
    else:
        new_status = "healthy"
    if new_status != s.status:
        if new_status in ("down", "stale", "degraded") and s.first_bad_wall_ts == 0.0:
            s.first_bad_wall_ts = now
        if new_status == "healthy":
            s.first_bad_wall_ts = 0.0
    s.status = new_status


def _probe_loop() -> None:
    """Tick freshness checks + fire notifications on transitions + cooldowns."""
    if _stop_event.wait(HEALTH_STARTUP_GRACE_S):
        return
    while not _stop_event.is_set():
        now = time.time()
        try:
            _probe_tick(now)
        except Exception:
            logger.exception("probe tick failed")
        if _stop_event.wait(HEALTH_PROBE_INTERVAL_S):
            return


def _probe_tick(now: float) -> None:
    # Ensure every configured source has a state object so "no events yet" is visible
    for src in sources_config.enabled_sources():
        with _state_lock:
            _get_source_state(src.id)

    to_notify: list[tuple[_SourceState, str]] = []
    recovered: list[_SourceState] = []
    with _state_lock:
        for s in _sources.values():
            _recompute_status_locked(s, now)
            if s.status in ("down", "stale", "degraded"):
                since_last = now - s.last_notified_wall_ts
                if s.last_notified_wall_ts == 0.0 or since_last >= HEALTH_REPEAT_S:
                    to_notify.append((s, s.status))
                    s.last_notified_wall_ts = now
            elif s.status == "healthy" and s.last_notified_wall_ts > 0.0:
                # Was previously notified as bad; announce recovery once
                recovered.append(s)
                s.last_notified_wall_ts = 0.0

    for s, status in to_notify:
        _dispatch_alert(s, status)
    for s in recovered:
        _dispatch_recovered(s)


def _dispatch_alert(s: _SourceState, status: str) -> None:
    title = f"source {s.source_id}: {status}"
    body_lines = [
        f"Source: {s.source_id}",
        f"Status: {status}",
        f"Last event: {_fmt_age(time.time() - s.last_event_wall_ts) if s.last_event_wall_ts else 'never'}",
    ]
    if s.last_segment_health not in ("ok", "unknown", ""):
        body_lines.append(f"Last segment health: {s.last_segment_health}")
    if s.last_segment_video_packets_per_s is not None:
        body_lines.append(f"Last video packets/s: {s.last_segment_video_packets_per_s:.2f}")
    if s.last_segment_path:
        body_lines.append(f"Last segment: {s.last_segment_path}")
    if s.last_error:
        body_lines.append(f"Error: {s.last_error}")
    body = "\n".join(body_lines)
    severity = "error" if status == "down" else "warning"
    try:
        notifications.send_all(title, body, severity)
    except Exception:
        logger.exception("notify fanout failed")
    logger.warning("ALERT %s %s", status, s.source_id)


def _dispatch_recovered(s: _SourceState) -> None:
    try:
        notifications.send_all(
            f"source {s.source_id}: recovered",
            f"Source {s.source_id} is back to healthy.",
            "info",
        )
    except Exception:
        logger.exception("recovery notify failed")
    logger.info("RECOVERED %s", s.source_id)


def _fmt_age(secs: float) -> str:
    if secs < 60: return f"{secs:.0f}s ago"
    if secs < 3600: return f"{secs/60:.1f}m ago"
    return f"{secs/3600:.1f}h ago"


def _consumer_loop() -> None:
    def handler(topic: str, entry_id: str, parsed: dict) -> None:
        mark_event(parsed.get("type") or topic,
                   parsed.get("source") or "",
                   parsed.get("payload") or {})
    try:
        events_bus.consume(
            topics=("source.health", "segment.written"),
            group="archivist-health-monitor",
            consumer=f"host-{os.getpid()}",
            handler=handler,
            stop_event=_stop_event,
            block_ms=2000,
            batch=32,
        )
    except Exception:
        logger.exception("consumer loop crashed")


def status() -> dict:
    """Snapshot for /health endpoint."""
    now = time.time()
    with _state_lock:
        sources = {}
        for s in _sources.values():
            _recompute_status_locked(s, now)
            sources[s.source_id] = {
                "status": s.status,
                "last_event_ts": s.last_event_wall_ts,
                "last_event_age_s": round(now - s.last_event_wall_ts, 1) if s.last_event_wall_ts else None,
                "last_health_state": s.last_health_state,
                "error": s.last_error,
                "last_segment_health": s.last_segment_health,
                "last_segment_path": s.last_segment_path,
                "last_segment_age_s": round(now - s.last_segment_written_ts, 1) if s.last_segment_written_ts else None,
                "last_segment_video_packets_per_s": s.last_segment_video_packets_per_s,
                "last_segment_video_duration_ratio": (
                    round(s.last_segment_video_duration_ratio, 3)
                    if s.last_segment_video_duration_ratio is not None
                    else None
                ),
            }
    overall = "healthy"
    for info in sources.values():
        if info["status"] == "down":
            overall = "error"; break
        if info["status"] in ("degraded", "stale", "unknown") and overall != "error":
            overall = "warning"
    return {
        "status": overall,
        "sources": sources,
        "started_at": _started_at,
        "channels": notifications.channels_configured(),
    }


def start() -> None:
    global _consumer_thread, _probe_thread, _started_at
    if _consumer_thread and _consumer_thread.is_alive():
        return
    _stop_event.clear()
    _started_at = time.time()
    _consumer_thread = threading.Thread(target=_consumer_loop, daemon=True, name="health-consumer")
    _consumer_thread.start()
    _probe_thread = threading.Thread(target=_probe_loop, daemon=True, name="health-probe")
    _probe_thread.start()
    logger.info(
        "health monitor started: stale=%.0fs probe=%.0fs repeat=%.0fs channels=%s",
        HEALTH_SOURCE_STALE_S, HEALTH_PROBE_INTERVAL_S, HEALTH_REPEAT_S,
        notifications.channels_configured(),
    )


def stop(timeout: float = 5.0) -> None:
    _stop_event.set()
    for t in (_consumer_thread, _probe_thread):
        if t is not None:
            t.join(timeout=timeout)
