"""GPU watchdog — periodic CUDA health probe with alerting.

Runs a background thread that checks torch.cuda availability every
GPU_WATCHDOG_INTERVAL_S seconds. On state transitions (ok -> lost, lost -> ok)
it fires notifications via the existing email + HA webhook channels and
publishes events to the event bus.

Public:
  start() / stop()           — lifecycle
  status() -> dict           — snapshot for /health
  gpu_ok() -> bool           — fast check for other services
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Optional

import notifications

logger = logging.getLogger("archivist.gpu_watchdog")

GPU_WATCHDOG_INTERVAL_S = float(os.getenv("GPU_WATCHDOG_INTERVAL_S", "30"))
GPU_WATCHDOG_STARTUP_GRACE_S = float(os.getenv("GPU_WATCHDOG_STARTUP_GRACE_S", "60"))
GPU_WATCHDOG_REPEAT_S = float(os.getenv("GPU_WATCHDOG_REPEAT_S", "1800"))

# Auto-recovery: if CUDA was healthy earlier this session and then goes missing
# for this long, restart the container (SIGTERM -> PID 1, brought back by compose
# restart=unless-stopped) so Whisper/vision/TTS get a fresh CUDA context. Nothing
# else auto-restarts this container, so a transient CUDA-context loss otherwise
# wedges transcription indefinitely (it has no CPU fallback). Guarded so a
# permanently-absent GPU does NOT crash-loop — see _trigger_container_restart.
GPU_WATCHDOG_EXIT_ON_LOSS = os.getenv("GPU_WATCHDOG_EXIT_ON_LOSS", "true").strip().lower() in ("1", "true", "yes", "on")
GPU_WATCHDOG_EXIT_AFTER_S = float(os.getenv("GPU_WATCHDOG_EXIT_AFTER_S", "180"))

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()

_state = "unknown"          # "ok" | "lost" | "unknown"
_last_check_ts: float = 0.0
_last_ok_ts: float = 0.0
_lost_since_ts: float = 0.0
_last_alert_ts: float = 0.0
_last_error: Optional[str] = None
_device_name: Optional[str] = None
_check_count: int = 0
_loss_count: int = 0
_exit_triggered: bool = False


def _probe_cuda() -> tuple[bool, Optional[str], Optional[str]]:
    """Returns (available, device_name, error_msg)."""
    try:
        import torch
    except ImportError:
        return False, None, "torch not installed"

    try:
        if not torch.cuda.is_available():
            return False, None, "torch.cuda.is_available() returned False"
        count = torch.cuda.device_count()
        if count == 0:
            return False, None, "device_count=0"
        idx = 0
        try:
            idx = int(os.getenv("TRANSCRIBE_GPU_ID", "0"))
        except (TypeError, ValueError):
            pass
        idx = min(idx, count - 1)
        name = torch.cuda.get_device_name(idx)
        # Smoke-test: allocate a tiny tensor and sync to confirm the GPU is responsive
        t = torch.zeros(1, device=f"cuda:{idx}")
        del t
        torch.cuda.synchronize(idx)
        return True, name, None
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def _on_gpu_lost(error: str) -> None:
    global _loss_count
    _loss_count += 1
    title = "GPU LOST — CUDA unavailable"
    body = (
        f"The GPU watchdog detected CUDA is no longer available.\n"
        f"Error: {error}\n"
        f"Last healthy: {_fmt_ts(_last_ok_ts)}\n"
        f"Loss count (this session): {_loss_count}\n"
        f"Host GPU ID: {os.getenv('TRANSCRIBE_GPU_ID', '0')}\n"
        f"NVIDIA_VISIBLE_DEVICES: {os.getenv('NVIDIA_VISIBLE_DEVICES', 'unset')}\n\n"
        f"Services affected: transcription (Whisper), vision (YOLO/CLIP), TTS.\n"
        f"Transcription may fall back to CPU (slow). Vision is offline."
    )
    try:
        notifications.send_all(title, body, severity="error")
    except Exception:
        logger.exception("GPU lost notification dispatch failed")
    logger.error("GPU LOST: %s", error)
    _publish_event("gpu.lost", {"error": error, "last_ok_ts": _last_ok_ts})


def _on_gpu_recovered(name: str) -> None:
    downtime = time.time() - _lost_since_ts if _lost_since_ts else 0
    title = "GPU RECOVERED — CUDA available"
    body = (
        f"The GPU watchdog confirmed CUDA is available again.\n"
        f"Device: {name}\n"
        f"Downtime: {_fmt_duration(downtime)}\n\n"
        f"NOTE: Services using the GPU (Whisper, YOLO, CLIP) may need the "
        f"container restarted to reclaim the device if they fell back to CPU."
    )
    try:
        notifications.send_all(title, body, severity="info")
    except Exception:
        logger.exception("GPU recovery notification dispatch failed")
    logger.info("GPU RECOVERED: %s (downtime %s)", name, _fmt_duration(downtime))
    _publish_event("gpu.recovered", {"device": name, "downtime_s": round(downtime, 1)})


def _on_gpu_still_lost(error: str) -> None:
    downtime = time.time() - _lost_since_ts if _lost_since_ts else 0
    title = "GPU STILL LOST — CUDA unavailable"
    body = (
        f"GPU has been unavailable for {_fmt_duration(downtime)}.\n"
        f"Error: {error}\n"
        f"Loss count (this session): {_loss_count}"
    )
    try:
        notifications.send_all(title, body, severity="error")
    except Exception:
        logger.exception("GPU repeat alert dispatch failed")
    logger.warning("GPU still lost (%s): %s", _fmt_duration(downtime), error)


def _trigger_container_restart(error: str, downtime: float) -> None:
    """Restart the container to reclaim a lost CUDA device.

    Called only after CUDA was healthy earlier this session and has now been
    unavailable for GPU_WATCHDOG_EXIT_AFTER_S. A long-lived process cannot get a
    broken CUDA context back without restarting, and nothing else auto-restarts
    this container, so we exit on purpose: SIGTERM to PID 1 (tini, via compose
    `init: true`) for a clean stop, and `restart: unless-stopped` brings it back
    with a fresh context. The "must have been healthy this session" guard (caller)
    means a permanently absent GPU will NOT loop — the next container never
    reaches "ok", so it never re-triggers.
    """
    global _exit_triggered
    if _exit_triggered:
        return
    _exit_triggered = True
    title = "GPU LOST — restarting container to reclaim CUDA"
    body = (
        f"CUDA was healthy earlier this session but has been unavailable for "
        f"{_fmt_duration(downtime)}.\nError: {error}\n\n"
        f"Restarting the container (SIGTERM -> PID 1) so Whisper/vision/TTS get a "
        f"fresh CUDA context; restart=unless-stopped will bring it back. The "
        f"watchdog restarts at most once per healthy->lost episode, so it will not "
        f"loop if CUDA is still gone after restart."
    )
    try:
        notifications.send_all(title, body, severity="error")
    except Exception:
        logger.exception("GPU restart notification dispatch failed")
    logger.critical(
        "GPU watchdog: CUDA lost for %s after prior health — sending SIGTERM to "
        "PID 1 to restart container (set GPU_WATCHDOG_EXIT_ON_LOSS=false to disable)",
        _fmt_duration(downtime),
    )
    try:
        import signal
        os.kill(1, signal.SIGTERM)
    except Exception:
        logger.exception("Failed to signal PID 1; falling back to os._exit(1)")
        os._exit(1)


def _publish_event(topic: str, payload: dict) -> None:
    try:
        import events_bus
        events_bus.publish(topic, "gpu_watchdog", payload)
    except Exception:
        logger.debug("event publish failed for %s", topic, exc_info=True)


def _watchdog_loop() -> None:
    global _state, _last_check_ts, _last_ok_ts, _lost_since_ts, _last_alert_ts
    global _last_error, _device_name, _check_count

    if _stop_event.wait(GPU_WATCHDOG_STARTUP_GRACE_S):
        return

    while not _stop_event.is_set():
        should_restart = False
        try:
            available, name, error = _probe_cuda()
            now = time.time()
            _last_check_ts = now
            _check_count += 1

            with _lock:
                prev = _state
                if available:
                    _state = "ok"
                    _last_ok_ts = now
                    _device_name = name
                    _last_error = None
                    if prev == "lost":
                        _on_gpu_recovered(name or "unknown")
                        _last_alert_ts = 0.0
                        _lost_since_ts = 0.0
                    elif prev == "unknown":
                        logger.info("GPU watchdog initial probe: ok (%s)", name)
                        _publish_event("gpu.ok", {"device": name})
                else:
                    _state = "lost"
                    _last_error = error
                    if prev != "lost":
                        _lost_since_ts = now
                        _on_gpu_lost(error or "unknown")
                        _last_alert_ts = now
                    elif (now - _last_alert_ts) >= GPU_WATCHDOG_REPEAT_S:
                        _on_gpu_still_lost(error or "unknown")
                        _last_alert_ts = now
                    # Auto-recover only if CUDA was healthy earlier this session
                    # (prevents a crash loop when the GPU is permanently absent).
                    if (
                        GPU_WATCHDOG_EXIT_ON_LOSS
                        and not _exit_triggered
                        and _last_ok_ts > 0
                        and _lost_since_ts > 0
                        and (now - _lost_since_ts) >= GPU_WATCHDOG_EXIT_AFTER_S
                    ):
                        should_restart = True
        except Exception:
            logger.exception("GPU watchdog tick failed")

        # Trigger outside the lock — send_all()/os.kill() must not block status().
        if should_restart:
            _trigger_container_restart(_last_error or "unknown", time.time() - _lost_since_ts)
            return

        if _stop_event.wait(GPU_WATCHDOG_INTERVAL_S):
            return


def gpu_ok() -> bool:
    return _state == "ok"


def status() -> dict:
    with _lock:
        return {
            "state": _state,
            "last_check_ts": _last_check_ts,
            "last_ok_ts": _last_ok_ts,
            "lost_since_ts": _lost_since_ts or None,
            "last_error": _last_error,
            "device_name": _device_name,
            "check_count": _check_count,
            "loss_count": _loss_count,
            "interval_s": GPU_WATCHDOG_INTERVAL_S,
            "repeat_alert_s": GPU_WATCHDOG_REPEAT_S,
            "exit_on_loss": GPU_WATCHDOG_EXIT_ON_LOSS,
            "exit_after_s": GPU_WATCHDOG_EXIT_AFTER_S,
            "exit_triggered": _exit_triggered,
        }


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_watchdog_loop, daemon=True, name="gpu-watchdog")
    _thread.start()
    logger.info(
        "GPU watchdog started: interval=%.0fs grace=%.0fs repeat=%.0fs "
        "exit_on_loss=%s exit_after=%.0fs channels=%s",
        GPU_WATCHDOG_INTERVAL_S,
        GPU_WATCHDOG_STARTUP_GRACE_S,
        GPU_WATCHDOG_REPEAT_S,
        GPU_WATCHDOG_EXIT_ON_LOSS,
        GPU_WATCHDOG_EXIT_AFTER_S,
        notifications.channels_configured(),
    )


def stop(timeout: float = 5.0) -> None:
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=timeout)


def _fmt_ts(ts: float) -> str:
    if not ts:
        return "never"
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _fmt_duration(secs: float) -> str:
    if secs < 60:
        return f"{secs:.0f}s"
    if secs < 3600:
        return f"{secs / 60:.1f}m"
    return f"{secs / 3600:.1f}h"
