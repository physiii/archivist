"""TTS streaming service for Archivist.

Runs an aiohttp WebSocket server alongside the main Flask app so clients can
receive streamed PCM audio. The server is booted in a background thread with
its own event loop at archivist startup.

Env vars:
  TTS_WS_PORT             Port for the aiohttp WS server (default 5051)
  TTS_MODEL_NAME          Coqui XTTS model (default xtts_v2)
  TTS_DEVICE_TYPE         auto | cuda | cpu (default auto)
  TTS_VOICE_NAME          Built-in speaker name (default Ana Florence)
  TTS_VOICE_SAMPLE        Path to a WAV file for voice cloning (optional)
  TTS_VOICE_LANGUAGE      BCP-47 language tag (default en)
  TTS_STREAM_SAMPLE_RATE  PCM sample rate sent to clients (default 24000)
  TTS_STREAM_CHUNK_SIZE   XTTS inference chunk size (default 35)
  TTS_PYTHON_PATH         Python path for external XTTS subprocess (optional)
  ENABLE_TTS_STREAMING    Set to 0/false to disable entirely (default true)
  TWIN_TTS_PREWARM        Set to 1/true to warm model at startup (default false)
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Optional

logger = logging.getLogger("archivist.tts")

# ── Configuration ────────────────────────────────────────────────────────

def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

TTS_WS_PORT = _env_int("TTS_WS_PORT", 5051)
TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")
TTS_DEVICE_TYPE = os.getenv("TTS_DEVICE_TYPE", "auto")
TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME", "Ana Florence")
TTS_VOICE_SAMPLE = os.getenv("TTS_VOICE_SAMPLE", "") or None
TTS_VOICE_LANGUAGE = os.getenv("TTS_VOICE_LANGUAGE", "en")
TTS_STREAM_SAMPLE_RATE = _env_int("TTS_STREAM_SAMPLE_RATE", 24000)
TTS_STREAM_CHUNK_SIZE = _env_int("TTS_STREAM_CHUNK_SIZE", 35)
ENABLE_TTS_STREAMING = _env_bool("ENABLE_TTS_STREAMING", True)
TTS_PREWARM = _env_bool("TWIN_TTS_PREWARM", False)

# ── Singletons ───────────────────────────────────────────────────────────

_speech_hub: Optional[object] = None
_speech_engine: Optional[object] = None
_speech_manager: Optional[object] = None
_loop: Optional[asyncio.AbstractEventLoop] = None
_started = False


def get_speech_manager():
    return _speech_manager


def get_speech_hub():
    return _speech_hub


def get_loop() -> Optional[asyncio.AbstractEventLoop]:
    return _loop


# ── aiohttp handlers ─────────────────────────────────────────────────────

async def _handle_tts(request):
    from aiohttp import web

    if _speech_manager is None:
        return web.json_response({"ok": False, "error": "speech_manager_disabled"})

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

    req_type = str(data.get("type") or "speak").strip().lower()
    room = str(data.get("room") or "default").strip() or "default"
    timeout = float(data.get("timeout", 60.0))

    try:
        if req_type == "notification":
            kind = str(data.get("kind") or "wake").strip() or "wake"
            ok = await asyncio.wait_for(
                _speech_manager.play_notification(
                    room=room,
                    kind=kind,
                    metadata={"source": "twin"},
                ),
                timeout=timeout,
            )
        else:
            text = str(data.get("text") or "").strip()
            if not text:
                return web.json_response({"ok": False, "error": "empty_text"}, status=400)
            allow_loopback = bool(data.get("allow_loopback", False))
            ok = await asyncio.wait_for(
                _speech_manager.speak(
                    text=text,
                    room=room,
                    allow_loopback=allow_loopback,
                    metadata={"source": "twin"},
                ),
                timeout=timeout,
            )
        payload = {"ok": bool(ok)}
        if not ok and _speech_engine is not None:
            try:
                status = _speech_engine.status() or {}
                error = status.get("error") or status.get("last_error")
                if error:
                    payload["error"] = str(error)
                payload["backend"] = {
                    key: status.get(key)
                    for key in ("backend", "ready", "device", "speaker_name", "model")
                    if key in status
                }
            except Exception:
                pass
        return web.json_response(payload)
    except asyncio.TimeoutError:
        return web.json_response({"ok": False, "error": "tts_timeout"})
    except Exception as exc:
        logger.exception("[tts] request failed")
        return web.json_response({"ok": False, "error": str(exc)}, status=500)


async def _handle_tts_status(request):
    from aiohttp import web

    if _speech_engine is None:
        return web.json_response({"enabled": False, "reason": "disabled"})
    client_counts = _speech_hub.client_counts() if _speech_hub is not None else {}
    return web.json_response(
        {
            "enabled": True,
            **_speech_engine.status(),
            "client_count": sum(client_counts.values()),
            "client_count_by_room": client_counts,
            "client_rooms": sorted(client_counts),
        }
    )


def _create_aiohttp_app():
    from aiohttp import web

    app = web.Application()
    if _speech_hub is not None:
        app.router.add_get("/ws/speech", _speech_hub.websocket_handler)
    app.router.add_post("/tts", _handle_tts)
    app.router.add_get("/tts/status", _handle_tts_status)
    return app


async def _run_server():
    from aiohttp import web

    app = _create_aiohttp_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", TTS_WS_PORT)
    await site.start()
    logger.info("[tts] aiohttp WS server listening on :%d", TTS_WS_PORT)
    # Run until the loop is stopped.
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def _thread_main():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    try:
        _loop.run_until_complete(_run_server())
    except Exception:
        logger.exception("[tts] aiohttp server crashed")
    finally:
        _loop.close()


# ── Public API ───────────────────────────────────────────────────────────

def start():
    """Initialize the TTS engine and boot the aiohttp WS server in a daemon thread.

    Safe to call multiple times (no-op after first call). Called from archivist's
    module-level startup block so gunicorn workers inherit it.
    """
    global _speech_hub, _speech_engine, _speech_manager, _started

    if _started:
        return
    _started = True

    if not ENABLE_TTS_STREAMING:
        logger.info("[tts] TTS streaming disabled (ENABLE_TTS_STREAMING=false)")
        return

    try:
        from speech_stream import SpeechStreamHub, StreamingTTSEngine, SpeechOrchestrator
    except ImportError as exc:
        logger.warning("[tts] Could not import speech_stream: %s — TTS disabled", exc)
        return

    _speech_hub = SpeechStreamHub(
        sample_rate=TTS_STREAM_SAMPLE_RATE,
        dtype="int16",
        channels=1,
    )
    _speech_engine = StreamingTTSEngine(
        model_name=TTS_MODEL_NAME,
        device_preference=TTS_DEVICE_TYPE,
        language=TTS_VOICE_LANGUAGE,
        speaker_name=TTS_VOICE_NAME,
        speaker_sample=TTS_VOICE_SAMPLE,
        chunk_size=TTS_STREAM_CHUNK_SIZE,
    )

    if not _speech_engine.is_available:
        logger.warning(
            "[tts] No TTS backend available (Coqui not installed, no external python, no espeak). "
            "WS server will still start but speak() will fail until a backend is configured."
        )

    _speech_manager = SpeechOrchestrator(
        engine=_speech_engine,
        hub=_speech_hub,
        enabled=True,
    )

    if TTS_PREWARM and _speech_engine.is_available:
        logger.info("[tts] Pre-warming TTS model in background")
        def _prewarm():
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            try:
                loop.run_until_complete(_speech_engine._ensure_ready())
                logger.info("[tts] TTS model warm")
            except Exception:
                logger.warning("[tts] TTS pre-warm failed (non-fatal)")
            finally:
                loop.close()
        threading.Thread(target=_prewarm, daemon=True, name="tts-prewarm").start()

    t = threading.Thread(target=_thread_main, daemon=True, name="tts-aiohttp")
    t.start()
    logger.info("[tts] Started aiohttp TTS server thread (port %d)", TTS_WS_PORT)
