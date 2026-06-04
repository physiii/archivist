"""
Utilities for turning LLM responses into streamed audio.

This module wires the Coqui XTTS v2 model into a websocket broadcast hub so
remote clients can play speech in sync with the room that triggered it.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import select
import shutil
import subprocess
import threading
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Tuple

import numpy as np
from aiohttp import WSMsgType, web
try:
    from torch.serialization import add_safe_globals
except ImportError:  # Older torch versions
    add_safe_globals = None

logger = logging.getLogger("archivist.speech")

# Global registry for noise suppression - rooms where TTS is active or recently finished
# Maps room -> timestamp when suppression should end
_noise_suppression_until: Dict[str, float] = {}
_noise_suppression_lock = asyncio.Lock()

# Recent TTS outputs per room (for LLM echo detection)
# Maps room -> list of (timestamp, text)
_recent_tts_outputs: Dict[str, list] = {}
_recent_tts_lock = asyncio.Lock()
RECENT_TTS_WINDOW = 30.0  # How long to remember TTS outputs (seconds)
RECENT_TTS_MAX_ENTRIES = 5  # Max entries per room

# How long to suppress transcription after TTS finishes (seconds)
# Increased from 3.0 to prevent feedback loops with ambient microphones
NOISE_SUPPRESSION_DURATION = 5.0
LOOPBACK_PRE_ROLL_SECONDS = float(os.getenv("TWIN_LOOPBACK_PRE_ROLL_SECONDS", "0.45"))
LOOPBACK_BETWEEN_CHUNKS_SECONDS = float(
    os.getenv("TWIN_LOOPBACK_BETWEEN_CHUNKS_SECONDS", "0.75")
)
LOOPBACK_GAIN = float(os.getenv("TWIN_LOOPBACK_GAIN", "1.6"))
LOOPBACK_REPEAT_COUNT = max(1, int(os.getenv("TWIN_LOOPBACK_REPEAT_COUNT", "2")))
LOOPBACK_MAX_TTS_CHARS = max(80, int(os.getenv("TWIN_LOOPBACK_MAX_TTS_CHARS", "220")))
FALLBACK_TTS_RATE_WPM = max(80, int(os.getenv("TWIN_FALLBACK_TTS_RATE_WPM", "150")))
FALLBACK_TTS_CHUNK_MS = max(20, int(os.getenv("TWIN_FALLBACK_TTS_CHUNK_MS", "80")))
FALLBACK_TTS_SAMPLE_RATE = max(8000, int(os.getenv("TWIN_FALLBACK_TTS_SAMPLE_RATE", "24000")))
ENABLE_LEGACY_FALLBACK_TTS = (
    os.getenv("TWIN_ALLOW_LEGACY_FALLBACK_TTS", "0").strip().lower()
    in ("1", "true", "yes", "on")
)
TTS_HELPER_BOOT_TIMEOUT_S = max(
    5.0,
    float(os.getenv("TWIN_TTS_HELPER_BOOT_TIMEOUT_S", "600.0")),
)
TTS_HELPER_RESPONSE_TIMEOUT_S = max(
    5.0,
    float(os.getenv("TWIN_TTS_HELPER_RESPONSE_TIMEOUT_S", "420.0")),
)
TTS_HELPER_MIN_FREE_VRAM_MB = max(
    1024,
    int(os.getenv("TWIN_TTS_HELPER_MIN_FREE_VRAM_MB", "4500")),
)
WEBSOCKET_SEND_TIMEOUT_S = max(
    0.2,
    float(os.getenv("TWIN_TTS_WEBSOCKET_SEND_TIMEOUT_S", "1.5")),
)
PCM_STREAM_FRAME_SECONDS = max(
    0.01,
    float(os.getenv("TWIN_TTS_STREAM_FRAME_SECONDS", "0.05")),
)


def _detect_fallback_tts_binary() -> Optional[str]:
    if not ENABLE_LEGACY_FALLBACK_TTS:
        return None
    configured = str(os.getenv("TWIN_FALLBACK_TTS_BIN") or "").strip()
    candidates = [configured] if configured else []
    candidates.extend(["espeak-ng", "espeak"])
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _prepare_loopback_tts_text(text: str) -> str:
    """Make test loopback speech easier for ASR to recover faithfully.

    The office audio E2E path speaks commands out loud, then relies on a room mic
    to hear them back. Compound power commands like
    "turn on the air conditioner and turn on the lights" are much more reliable
    when XTTS gets an explicit clause break instead of a flat conjunction.
    Keep the wording semantically identical; only add punctuation/spacing.
    """
    normalized = re.sub(r"\s+", " ", str(text or "").strip())
    if not normalized:
        return ""
    lowered = normalized.lower()
    simple_power_aliases = {
        "turn on the lights": "lights on. turn on the lights.",
        "turn off the lights": "lights off. turn off the lights.",
        "turn on the air conditioner": "air conditioner on. turn on the air conditioner.",
        "turn off the air conditioner": "air conditioner off. turn off the air conditioner.",
    }
    if lowered in simple_power_aliases:
        return simple_power_aliases[lowered]
    temp_match = re.match(
        r"^set (?:the )?(?:temperature|thermostat|climate) to (?P<temp>[a-z0-9\-\s]+?)(?: degrees?)?$",
        lowered,
    )
    if temp_match:
        temp_phrase = " ".join(str(temp_match.group("temp") or "").split())
        if temp_phrase:
            return f"set the temperature to {temp_phrase} degrees. temperature {temp_phrase} degrees."
    compound_segments = [
        part.strip(" \t\r\n,.;:!?")
        for part in re.split(r"\s+(?:and|then)\s+|(?<=[.!?])\s+", normalized, flags=re.IGNORECASE)
        if str(part or "").strip()
    ]
    if len(compound_segments) >= 2:
        expanded_segments = []
        used_alias = False
        for segment in compound_segments:
            alias = simple_power_aliases.get(segment.lower())
            if alias:
                expanded_segments.append(alias.rstrip())
                used_alias = True
            else:
                expanded_segments.append(segment)
        if used_alias:
            return " ".join(expanded_segments)
    color_aliases = {
        "blue",
        "red",
        "green",
        "white",
        "warm white",
        "cool white",
        "purple",
        "pink",
        "yellow",
        "orange",
    }
    for pattern in (
        r"^set (?:the )?lights to (?P<color>.+)$",
        r"^set (?:the )?lights (?P<color>.+)$",
        r"^make (?:the )?lights (?P<color>.+)$",
    ):
        match = re.match(pattern, lowered)
        if not match:
            continue
        color = " ".join(str(match.group("color") or "").split())
        if color in color_aliases:
            # Short color commands are prone to collapsing into a single vowel-like
            # syllable under XTTS+ASR loopback. Keep the semantic content identical
            # while naming "the color" twice so the ASR path preserves the target hue.
            return f"set the lights to the color {color}. color {color}."
    # Insert a sentence break before repeated imperative power clauses so the TTS
    # voice renders them as distinct actions and the transcript preserves both.
    clarified = re.sub(
        r"\s+(?:and|then)\s+((?:turn|switch|power|shut)\s+(?:on|off)\b)",
        r". \1",
        normalized,
        flags=re.IGNORECASE,
    )
    return clarified


def _prepare_loopback_tts_chunks(text: str) -> list[str]:
    """Split compound loopback commands into distinct TTS chunks.

    The room-mic E2E tests do better when each imperative clause is synthesized
    separately with a short pause. This only applies to `allow_loopback=True`,
    so it does not change normal user-facing TTS.
    """
    clarified = _prepare_loopback_tts_text(text)
    if not clarified:
        return []
    parts = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", clarified)
        if str(part or "").strip()
    ]
    power_clause_count = sum(
        1
        for part in parts
        if re.search(r"\b(?:turn|switch|power|shut)\s+(?:on|off)\b", part, flags=re.IGNORECASE)
    )
    shorthand_clause_count = sum(
        1
        for part in parts
        if re.search(r"\b(?:air conditioner|lights?)\s+(?:on|off)\b", part, flags=re.IGNORECASE)
    )
    if len(parts) >= 2 and (power_clause_count >= 2 or shorthand_clause_count >= 1):
        return parts
    if len(clarified) > LOOPBACK_MAX_TTS_CHARS and len(parts) >= 2:
        chunks: list[str] = []
        current = ""
        for part in parts:
            if current and len(current) + 1 + len(part) <= LOOPBACK_MAX_TTS_CHARS:
                current = f"{current} {part}"
                continue
            if current:
                chunks.append(current)
            current = part
        if current:
            chunks.append(current)
        return chunks
    return [clarified]


def _prepare_loopback_playback_chunks(text: str) -> list[str]:
    """Expand loopback chunks for more reliable room-mic recovery.

    A short office speaker->mic path often clips the first few syllables of a
    single-clause utterance. Repeating simple loopback phrases gives the mic a
    second clean shot without changing normal user-facing TTS. Compound power
    commands benefit from the same treatment per clause.
    """
    chunks = _prepare_loopback_tts_chunks(text)
    if LOOPBACK_REPEAT_COUNT <= 1 or not chunks:
        return chunks
    clarified = _prepare_loopback_tts_text(text)
    if len(clarified) > LOOPBACK_MAX_TTS_CHARS and len(chunks) >= 2:
        return chunks
    repeated: list[str] = []
    for chunk in chunks:
        repeated.extend([chunk] * LOOPBACK_REPEAT_COUNT)
    return repeated


async def record_tts_output(room: str, text: str):
    """Record a TTS output for echo detection."""
    import time
    async with _recent_tts_lock:
        if room not in _recent_tts_outputs:
            _recent_tts_outputs[room] = []
        _recent_tts_outputs[room].append((time.time(), text))
        # Prune old entries
        cutoff = time.time() - RECENT_TTS_WINDOW
        _recent_tts_outputs[room] = [
            (ts, t) for ts, t in _recent_tts_outputs[room]
            if ts > cutoff
        ][-RECENT_TTS_MAX_ENTRIES:]


def get_recent_tts_outputs(room: str, max_entries: int = 3) -> list:
    """Get recent TTS outputs for a room (for LLM echo detection)."""
    import time
    entries = _recent_tts_outputs.get(room, [])
    cutoff = time.time() - RECENT_TTS_WINDOW
    valid = [(ts, t) for ts, t in entries if ts > cutoff]
    return [t for _, t in valid[-max_entries:]]


def is_tts_echo_text(room: str, text: str, *, threshold: int = 75) -> bool:
    """
    Best-effort echo detection: returns True if `text` looks like recent TTS output for `room`.

    Uses token_set_ratio which handles word reordering well - critical because
    ASR often transcribes TTS echoes with words in different order.
    E.g., TTS: "Backyard Temp Temperature is 67.03 degrees fahrenheit"
          ASR: "67.03 to Fahrenheit. Backyard temp temperature."
    Also treats "didn't respond / try again" style phrases as echo when recent TTS said the same.
    """
    import re
    text = (text or "").strip()
    if not text:
        return False
    recent = get_recent_tts_outputs(room, max_entries=3) or []
    if not recent:
        return False
    # Suppress re-transcribed failure messages (e.g. "office light didn't response try again")
    lowered = (text or "").lower()
    if ("try again" in lowered or "didn't respond" in lowered or "didnt respond" in lowered) and len(text) < 80:
        for tts in recent:
            if tts and ("try again" in (tts or "").lower() or "didn't respond" in (tts or "").lower()):
                return True
    try:
        from rapidfuzz import fuzz  # type: ignore
        # token_set_ratio handles word reordering better than partial_ratio
        scorer = fuzz.token_set_ratio
    except Exception:  # pragma: no cover - dependency optional
        scorer = None

    # Normalize aggressively: ASR often drops punctuation while TTS includes it.
    def norm(s: str) -> str:
        s = (s or "").lower()
        return re.sub(r"[^a-z0-9]+", " ", s).strip()

    lowered = norm(text)
    for tts in recent:
        tts = (tts or "").strip()
        if not tts:
            continue
        tts_norm = norm(tts)
        if scorer is not None:
            try:
                if scorer(lowered, tts_norm) >= threshold:
                    return True
            except Exception:
                continue
        else:
            # Fallback to simple containment when rapidfuzz is unavailable.
            if lowered in tts_norm or tts_norm in lowered:
                return True
    return False


def is_tts_echo_text_global(text: str, *, threshold: int = 70) -> bool:
    """
    Check if text matches recent TTS output from ANY room.
    
    Uses token_set_ratio for robust matching of reordered/partial transcriptions.
    Lower threshold (70) for global check to catch more echoes.
    Also suppresses re-transcribed "didn't respond / try again" style phrases.
    """
    import time
    import re
    text = (text or "").strip()
    if not text or len(text) < 10:
        return False
    lowered_raw = (text or "").lower()
    if ("try again" in lowered_raw or "didn't respond" in lowered_raw or "didnt respond" in lowered_raw) and len(text) < 80:
        cutoff = time.time() - RECENT_TTS_WINDOW
        for room, entries in _recent_tts_outputs.items():
            for ts, tts in entries:
                if ts < cutoff or not tts:
                    continue
                if "try again" in (tts or "").lower() or "didn't respond" in (tts or "").lower():
                    return True
    
    try:
        from rapidfuzz import fuzz
        # token_set_ratio handles word reordering better than partial_ratio
        scorer = fuzz.token_set_ratio
    except Exception:
        scorer = None
    
    def norm(s: str) -> str:
        s = (s or "").lower()
        return re.sub(r"[^a-z0-9]+", " ", s).strip()

    lowered = norm(text)
    cutoff = time.time() - RECENT_TTS_WINDOW
    
    # Check all rooms
    for room, entries in _recent_tts_outputs.items():
        for ts, tts in entries:
            if ts < cutoff:
                continue
            tts = (tts or "").strip()
            if not tts:
                continue
            tts_lower = norm(tts)
            
            if scorer is not None:
                try:
                    if scorer(lowered, tts_lower) >= threshold:
                        return True
                except Exception:
                    continue
            else:
                if lowered in tts_lower or tts_lower in lowered:
                    return True
    return False


async def set_noise_suppression(room: str, duration: float = NOISE_SUPPRESSION_DURATION):
    """Mark a room as having active/recent TTS output."""
    import time
    async with _noise_suppression_lock:
        _noise_suppression_until[room] = time.time() + duration


async def is_noise_suppressed(room: str) -> bool:
    """Check if a room should suppress transcription due to recent TTS."""
    import time
    async with _noise_suppression_lock:
        until = _noise_suppression_until.get(room, 0)
        return time.time() < until


def get_noise_suppression_remaining(room: str) -> float:
    """Get remaining suppression time for a room (non-async for logging)."""
    import time
    until = _noise_suppression_until.get(room, 0)
    remaining = until - time.time()
    return max(0, remaining)


def _xtts_worker_script_path() -> Path:
    return Path(__file__).with_name("xtts_worker.py")


def _best_cuda_device_index(*, min_free_mb: int) -> Optional[int]:
    # Prefer torch.cuda (same driver API that already works for Whisper) over
    # shelling out to `nvidia-smi`. NVML-via-CLI can fail inside containers
    # after cgroup reloads even when the CUDA driver itself is healthy, which
    # would otherwise silently push xtts onto CPU.
    try:
        import torch
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            best_index = None
            best_free = -1
            for idx in range(torch.cuda.device_count()):
                try:
                    free_bytes, _total = torch.cuda.mem_get_info(idx)
                except Exception:
                    continue
                free_mb = int(free_bytes // (1024 * 1024))
                if free_mb < int(min_free_mb):
                    continue
                if free_mb > best_free:
                    best_free = free_mb
                    best_index = idx
            if best_index is not None:
                return best_index
    except Exception:
        pass

    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None
    try:
        proc = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=index,memory.free",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None

    best_index = None
    best_free = -1
    for line in (proc.stdout or "").splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            index = int(parts[0])
            free_mb = int(float(parts[1]))
        except Exception:
            continue
        if free_mb < int(min_free_mb):
            continue
        if free_mb > best_free:
            best_free = free_mb
            best_index = index
    return best_index


def _resolve_external_tts_launch(device_preference: str) -> dict:
    pref = str(device_preference or "auto").strip().lower()
    if pref in {"", "auto", "cuda"}:
        if pref == "cuda":
            best_index = _best_cuda_device_index(min_free_mb=TTS_HELPER_MIN_FREE_VRAM_MB)
            if best_index is None:
                return {"device": "cpu", "visible_device": None, "resolved": "cpu"}
            return {"device": "cuda", "visible_device": str(best_index), "resolved": f"cuda:{best_index}"}

        best_index = _best_cuda_device_index(min_free_mb=TTS_HELPER_MIN_FREE_VRAM_MB)
        if best_index is not None:
            return {"device": "cuda", "visible_device": str(best_index), "resolved": f"cuda:{best_index}"}
        return {"device": "cpu", "visible_device": None, "resolved": "cpu"}
    if pref.startswith("cuda:"):
        return {
            "device": "cuda",
            "visible_device": pref.split(":", 1)[1],
            "resolved": pref,
        }
    return {"device": pref or "cpu", "visible_device": None, "resolved": pref or "cpu"}


# Ensure Coqui downloads do not prompt for interactive license confirmation.
os.environ.setdefault("COQUI_TOS_AGREED", "1")
os.environ.setdefault("COQUI_LANG", "en")

# Transformers 4.45+ moved BeamSearchScorer; patch top-level namespace so Coqui still imports.
def _patch_beam_scorer():
    """Ensure transformers exposes the generation symbols XTTS expects."""
    try:
        import transformers  # type: ignore
        from transformers.generation.beam_constraints import DisjunctiveConstraint, PhrasalConstraint  # type: ignore
        from transformers.generation.beam_search import BeamSearchScorer, ConstrainedBeamSearchScorer  # type: ignore
        from transformers.generation.configuration_utils import GenerationConfig  # type: ignore
        from transformers.generation.logits_process import LogitsProcessorList  # type: ignore
        from transformers.generation.stopping_criteria import StoppingCriteriaList  # type: ignore
        from transformers.generation.utils import GenerationMixin  # type: ignore
        from transformers.modeling_utils import PreTrainedModel  # type: ignore
    except Exception:
        logger.warning("[speech] Unable to import transformers generation compatibility symbols")
        return None

    compatibility_exports = {
        "BeamSearchScorer": BeamSearchScorer,
        "ConstrainedBeamSearchScorer": ConstrainedBeamSearchScorer,
        "DisjunctiveConstraint": DisjunctiveConstraint,
        "GenerationConfig": GenerationConfig,
        "GenerationMixin": GenerationMixin,
        "LogitsProcessorList": LogitsProcessorList,
        "PhrasalConstraint": PhrasalConstraint,
        "PreTrainedModel": PreTrainedModel,
        "StoppingCriteriaList": StoppingCriteriaList,
    }
    for name, value in compatibility_exports.items():
        setattr(transformers, name, value)
    logger.info("[speech] Patched transformers generation exports for Coqui compatibility")
    return BeamSearchScorer


_patch_beam_scorer()


def _patch_validate_model_class():
    """Patch XTTS' GPT2InferenceModel for newer transformers releases."""
    try:
        from transformers.generation.utils import GenerationMixin  # type: ignore
        from TTS.tts.layers.xtts.gpt_inference import GPT2InferenceModel  # type: ignore
    except Exception:
        return  # TTS not installed or different version
    if GenerationMixin not in GPT2InferenceModel.__mro__:
        try:
            GPT2InferenceModel.__bases__ = (GenerationMixin,) + GPT2InferenceModel.__bases__
            logger.info("[speech] Patched GPT2InferenceModel bases with GenerationMixin")
        except Exception as exc:
            logger.warning(f"[speech] Failed to patch GPT2InferenceModel bases: {exc}")
    if not hasattr(GPT2InferenceModel, "_validate_model_class"):
        GPT2InferenceModel._validate_model_class = lambda self: None
        logger.info("[speech] Patched GPT2InferenceModel._validate_model_class for transformers >=4.50 compat")


_patch_validate_model_class()

torch = None  # type: ignore
XttsConfig = Xtts = ModelManager = get_user_data_dir = XttsAudioConfig = BaseDatasetConfig = XttsArgs = None  # type: ignore
_TTS_IMPORT_ERROR: Optional[Exception] = None
HAS_TTS = False
_TTS_BACKEND_SETTING = os.getenv("TWIN_TTS_BACKEND", "auto").strip().lower() or "auto"
_SKIP_INPROCESS_TTS_IMPORT = _TTS_BACKEND_SETTING in {
    "fallback",
    "legacy_fallback",
    "espeak",
    "espeak-ng",
    "external",
    "xtts_external",
}


def _import_tts_modules() -> bool:
    """Import Coqui XTTS dependencies with optional retry."""
    global torch, XttsConfig, Xtts, ModelManager, get_user_data_dir, XttsAudioConfig, BaseDatasetConfig, XttsArgs, _TTS_IMPORT_ERROR
    try:
        import torch as torch_mod
        from TTS.tts.layers.xtts import stream_generator as _xtts_stream_generator  # noqa: F401
        from TTS.tts.configs.xtts_config import XttsConfig as XttsConfigMod
        from TTS.tts.models.xtts import Xtts as XttsMod, XttsAudioConfig as XttsAudioConfigMod, XttsArgs as XttsArgsMod
        from TTS.utils.generic_utils import get_user_data_dir as get_user_data_dir_mod
        from TTS.utils.manage import ModelManager as ModelManagerMod
        try:
            from TTS.config.shared_configs import BaseDatasetConfig as BaseDatasetConfigMod
        except Exception:
            BaseDatasetConfigMod = None
    except Exception as exc:  # pragma: no cover - handled gracefully
        _TTS_IMPORT_ERROR = exc
        return False

    torch = torch_mod
    XttsConfig = XttsConfigMod
    Xtts = XttsMod
    get_user_data_dir = get_user_data_dir_mod
    ModelManager = ModelManagerMod
    XttsAudioConfig = XttsAudioConfigMod
    BaseDatasetConfig = BaseDatasetConfigMod
    XttsArgs = XttsArgsMod
    if add_safe_globals:
        try:
            safe_classes = [cls for cls in (XttsConfigMod, XttsAudioConfigMod, BaseDatasetConfigMod, XttsArgsMod) if cls]
            if safe_classes:
                add_safe_globals(safe_classes)
                logger.debug(f"[speech] Registered {len(safe_classes)} safe globals for XTTS checkpoint loading")
        except Exception as exc:
            logger.warning(f"[speech] Failed to register safe globals for XTTS config: {exc}")
    else:
        logger.debug("[speech] torch.serialization.add_safe_globals unavailable; falling back to weights_only=False")
    _TTS_IMPORT_ERROR = None
    return True


HAS_TTS = False if _SKIP_INPROCESS_TTS_IMPORT else _import_tts_modules()
if not HAS_TTS and _TTS_IMPORT_ERROR and "BeamSearchScorer" in str(_TTS_IMPORT_ERROR):
    # Patch transformers and retry once for BeamSearchScorer import errors
    _patch_beam_scorer()
    HAS_TTS = _import_tts_modules()

if _SKIP_INPROCESS_TTS_IMPORT:
    logger.info("[speech] Skipping in-process XTTS import because TWIN_TTS_BACKEND=%s", _TTS_BACKEND_SETTING)
elif not HAS_TTS and _TTS_IMPORT_ERROR:
    logger.warning("[speech] Coqui TTS unavailable: %s", _TTS_IMPORT_ERROR)


class SpeechStreamHub:
    """Manages websocket clients that are ready to receive PCM audio frames."""

    def __init__(self, sample_rate: int = 24000, dtype: str = "int16", channels: int = 1):
        self.sample_rate = sample_rate
        self.dtype = dtype
        self.channels = channels
        self._clients: Dict[str, set[web.WebSocketResponse]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def _register(self, room: str, ws: web.WebSocketResponse):
        async with self._lock:
            self._clients[room].add(ws)

    async def _unregister(self, room: str, ws: web.WebSocketResponse):
        async with self._lock:
            if room in self._clients:
                self._clients[room].discard(ws)
                if not self._clients[room]:
                    self._clients.pop(room, None)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Accept websocket connections and map them to rooms."""
        room = request.query.get("room")
        client_id = request.query.get("client_id") or str(uuid.uuid4())
        ingress = str(request.query.get("ingress") or request.query.get("mode") or "").strip().lower() in {"1", "true", "yes", "ingress", "source"}
        if not room:
            raise web.HTTPBadRequest(text="room query parameter is required")

        ws = web.WebSocketResponse(heartbeat=20.0)
        await ws.prepare(request)

        if ingress:
            logger.info(f"[speech] Ingress {client_id} registered for room '{room}'")
            await ws.send_json(
                {
                    "type": "ready",
                    "room": room,
                    "client_id": client_id,
                    "sample_rate": self.sample_rate,
                    "sample_format": self.dtype,
                    "channels": self.channels,
                    "client_count": self.client_count(room),
                    "ingress": True,
                }
            )

            try:
                async for msg in ws:
                    if msg.type == WSMsgType.BINARY:
                        if msg.data:
                            await self.broadcast_audio(room, msg.data)
                            await ws.send_json(
                                {
                                    "type": "chunk",
                                    "room": room,
                                    "bytes": len(msg.data),
                                    "client_count": self.client_count(room),
                                }
                            )
                    elif msg.type == WSMsgType.TEXT:
                        if msg.data == "ping":
                            await ws.send_str("pong")
                            continue
                        try:
                            payload = json.loads(msg.data)
                        except Exception:
                            payload = {}
                        msg_type = str(payload.get("type") or "").strip().lower()
                        if msg_type == "stop":
                            break
                        if msg_type in {"start", "end", "error"}:
                            await self.broadcast_control(room, payload)
                    elif msg.type == WSMsgType.ERROR:
                        logger.warning(f"[speech] Ingress {client_id} error: {ws.exception()}")
                        break
            finally:
                await ws.close()
                logger.info(f"[speech] Ingress {client_id} disconnected from room '{room}'")

            return ws

        await self._register(room, ws)
        logger.info(f"[speech] Client {client_id} registered for room '{room}'")

        await ws.send_json(
            {
                "type": "ready",
                "room": room,
                "client_id": client_id,
                "sample_rate": self.sample_rate,
                "sample_format": self.dtype,
                "channels": self.channels,
            }
        )

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT and msg.data == "ping":
                    await ws.send_str("pong")
                elif msg.type == WSMsgType.ERROR:
                    logger.warning(f"[speech] Client {client_id} error: {ws.exception()}")
                    break
        finally:
            await self._unregister(room, ws)
            await ws.close()
            logger.info(f"[speech] Client {client_id} disconnected from room '{room}'")

        return ws

    def client_count(self, room: str) -> int:
        return len(self._clients.get(room, ()))

    def client_counts(self) -> Dict[str, int]:
        return {room: len(clients) for room, clients in self._clients.items()}

    async def _broadcast(
        self,
        room: str,
        send_fn,
        payload,
    ):
        """Send payload to all clients for a room with auto-cleanup."""
        targets = list(self._clients.get(room, ()))
        if not targets:
            return

        stale: list[web.WebSocketResponse] = []
        for ws in targets:
            try:
                await asyncio.wait_for(send_fn(ws, payload), timeout=WEBSOCKET_SEND_TIMEOUT_S)
            except Exception as exc:  # pragma: no cover - network specific
                logger.debug(f"[speech] Dropping websocket: {exc}")
                stale.append(ws)

        # Remove stale clients after broadcast
        for ws in stale:
            await self._unregister(room, ws)

    async def broadcast_control(self, room: str, payload: Dict):
        await self._broadcast(room, lambda ws, data: ws.send_json(data), payload)

    async def broadcast_audio(self, room: str, chunk: bytes):
        await self._broadcast(room, lambda ws, data: ws.send_bytes(data), chunk)


class ExternalXTTSBackend:
    """Bridge Twin's speech path to a dedicated XTTS virtualenv."""

    def __init__(
        self,
        *,
        python_path: str,
        model_name: str,
        language: str,
        speaker_name: Optional[str],
        speaker_sample: Optional[str],
        device_preference: str,
    ):
        self.python_path = str(python_path or "").strip()
        self.model_name = model_name
        self.language = language
        self.speaker_name = str(speaker_name or "").strip() or "Ana Florence"
        self.speaker_sample = str(speaker_sample or "").strip() or None
        self.device_preference = str(device_preference or "auto").strip() or "auto"
        self.helper_script = _xtts_worker_script_path()
        self._proc: Optional[subprocess.Popen] = None
        self._io_lock = threading.Lock()
        self._start_lock = threading.Lock()
        self._status: dict = {
            "backend": "xtts_external",
            "configured": bool(self.python_path and os.path.isfile(self.python_path) and self.helper_script.is_file()),
            "ready": False,
            "model": self.model_name,
            "language": self.language,
            "speaker_name": self.speaker_name,
            "speaker_sample": self.speaker_sample,
            "device_preference": self.device_preference,
            "device": None,
            "error": None,
            "helper_script": str(self.helper_script),
            "python_path": self.python_path,
        }

    @property
    def is_configured(self) -> bool:
        return bool(self._status.get("configured"))

    def _read_response_locked(self, timeout_s: float) -> dict:
        if not self._proc or not self._proc.stdout:
            raise RuntimeError("xtts_helper_not_running")
        fd = self._proc.stdout.fileno()
        deadline = time.monotonic() + max(0.0, float(timeout_s))
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"xtts_helper_timeout:{timeout_s:.1f}s")
            ready, _, _ = select.select([fd], [], [], remaining)
            if not ready:
                raise TimeoutError(f"xtts_helper_timeout:{timeout_s:.1f}s")
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("xtts_helper_closed_stdout")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("[speech] Ignoring non-JSON XTTS helper stdout: %s", str(line).strip()[:300])
                continue
            if not isinstance(payload, dict):
                logger.warning("[speech] Ignoring invalid XTTS helper payload: %r", payload)
                continue
            return payload

    def _terminate_locked(self) -> None:
        proc = self._proc
        self._proc = None
        self._status["ready"] = False
        if not proc:
            return
        try:
            if proc.stdin:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _ensure_started_sync(self) -> None:
        if not self.is_configured:
            raise RuntimeError("xtts_helper_unconfigured")
        with self._start_lock:
            if self._proc and self._proc.poll() is None:
                return
            self._terminate_locked()
            launch = _resolve_external_tts_launch(self.device_preference)
            env = os.environ.copy()
            if launch.get("visible_device") is not None and "CUDA_VISIBLE_DEVICES" not in env:
                env["CUDA_VISIBLE_DEVICES"] = str(launch["visible_device"])
            cmd = [
                self.python_path,
                str(self.helper_script),
                "--model",
                self.model_name,
                "--language",
                self.language,
                "--speaker-name",
                self.speaker_name,
                "--device",
                str(launch["device"]),
            ]
            if self.speaker_sample:
                cmd.extend(["--speaker-sample", self.speaker_sample])
            logger.info(
                "[speech] Starting external XTTS helper via %s (%s)",
                self.python_path,
                launch["resolved"],
            )
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                text=True,
                bufsize=1,
                env=env,
            )
            try:
                ready = self._read_response_locked(TTS_HELPER_BOOT_TIMEOUT_S)
            except Exception:
                self._terminate_locked()
                raise
            self._status.update(ready)
            self._status["configured"] = True
            self._status["device"] = ready.get("device") or launch["resolved"]
            self._status["ready"] = bool(ready.get("ok"))
            if not ready.get("ok"):
                self._status["error"] = ready.get("error") or "xtts_helper_start_failed"
                self._terminate_locked()
                raise RuntimeError(str(self._status["error"]))

    def synthesize_sync(self, text: str) -> tuple[np.ndarray, int]:
        self._ensure_started_sync()
        with self._io_lock:
            if not self._proc or self._proc.poll() is not None:
                self._terminate_locked()
                self._ensure_started_sync()
            assert self._proc is not None
            assert self._proc.stdin is not None
            payload = {"type": "synthesize", "text": text}
            self._proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            self._proc.stdin.flush()
            response = self._read_response_locked(TTS_HELPER_RESPONSE_TIMEOUT_S)
            status_response = {k: v for k, v in response.items() if k != "audio_b64"}
            self._status.update(status_response)
            self._status["ready"] = bool(response.get("ok"))
            self._status["error"] = response.get("error")
            if not response.get("ok"):
                raise RuntimeError(str(response.get("error") or "xtts_helper_synthesize_failed"))
            encoded = str(response.get("audio_b64") or "")
            audio = np.frombuffer(base64.b64decode(encoded), dtype="<f4").copy()
            sample_rate = int(response.get("sample_rate") or FALLBACK_TTS_SAMPLE_RATE)
            return audio, sample_rate

    def status(self) -> dict:
        return dict(self._status)


class StreamingTTSEngine:
    """
    Wraps Coqui XTTS-v2 streaming so callers can iterate over PCM chunks.
    Falls back gracefully when the dependency is not present.
    """

    def __init__(
        self,
        model_name: str,
        device_preference: str = "auto",
        language: str = "en",
        speaker_name: Optional[str] = "Ana Florence",
        speaker_sample: Optional[str] = None,
        chunk_size: int = 35,
    ):
        self.model_name = model_name
        self.language = language
        self.speaker_name = speaker_name
        self.speaker_sample = speaker_sample
        self.chunk_size = chunk_size
        self._model: Optional[Xtts] = None
        self._config: Optional[XttsConfig] = None
        self._conditioning: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
        self._load_lock = asyncio.Lock()
        self._device_preference = device_preference
        self._backend_preference = (
            os.getenv("TWIN_TTS_BACKEND", "auto").strip().lower() or "auto"
        )
        self._fallback_tts_bin = _detect_fallback_tts_binary()
        self._fallback_voice = str(os.getenv("TWIN_FALLBACK_TTS_VOICE") or "").strip()
        self._external_backend = ExternalXTTSBackend(
            python_path=str(os.getenv("TTS_PYTHON_PATH") or "").strip(),
            model_name=model_name,
            language=language,
            speaker_name=speaker_name,
            speaker_sample=speaker_sample,
            device_preference=device_preference,
        )
        self._last_error: Optional[str] = None

        if torch is not None:
            if device_preference == "auto":
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.device = torch.device(device_preference)
        else:  # pragma: no cover - import failure path
            self.device = None  # type: ignore

    def _force_legacy_fallback(self) -> bool:
        return self._backend_preference in {"fallback", "legacy_fallback", "espeak", "espeak-ng"}

    def _force_external_backend(self) -> bool:
        return self._backend_preference in {"external", "xtts_external"}

    def _allow_inprocess_xtts(self) -> bool:
        return self._backend_preference in {"auto", "inprocess", "xtts", "xtts_inprocess"}

    @property
    def is_available(self) -> bool:
        if self._force_legacy_fallback():
            return self._fallback_tts_bin is not None
        if self._force_external_backend():
            return self._external_backend.is_configured
        return HAS_TTS or self._external_backend.is_configured or self._fallback_tts_bin is not None

    def status(self) -> dict:
        if self._force_legacy_fallback():
            return {
                "backend": "legacy_fallback" if self._fallback_tts_bin else "disabled",
                "configured": bool(self._fallback_tts_bin),
                "ready": bool(self._fallback_tts_bin),
                "model": self.model_name,
                "language": self.language,
                "speaker_name": self.speaker_name,
                "speaker_sample": self.speaker_sample,
                "device": "cpu" if self._fallback_tts_bin else None,
                "error": self._last_error or (None if self._fallback_tts_bin else "legacy_fallback_unavailable"),
            }
        if self._force_external_backend():
            return self._external_backend.status() if self._external_backend.is_configured else {
                "backend": "disabled",
                "configured": False,
                "ready": False,
                "model": self.model_name,
                "language": self.language,
                "speaker_name": self.speaker_name,
                "speaker_sample": self.speaker_sample,
                "device": None,
                "error": self._last_error or "external_tts_unavailable",
            }
        if HAS_TTS and self._allow_inprocess_xtts():
            return {
                "backend": "xtts_inprocess",
                "configured": True,
                "ready": self._model is not None,
                "model": self.model_name,
                "language": self.language,
                "speaker_name": self.speaker_name,
                "speaker_sample": self.speaker_sample,
                "device": str(self.device) if self.device is not None else None,
                "error": self._last_error or (_TTS_IMPORT_ERROR and str(_TTS_IMPORT_ERROR)) or None,
            }
        if self._external_backend.is_configured:
            return self._external_backend.status()
        return {
            "backend": "legacy_fallback" if self._fallback_tts_bin else "disabled",
            "configured": bool(self._fallback_tts_bin),
            "ready": bool(self._fallback_tts_bin),
            "model": self.model_name,
            "language": self.language,
            "speaker_name": self.speaker_name,
            "speaker_sample": self.speaker_sample,
            "device": "cpu" if self._fallback_tts_bin else None,
            "error": self._last_error or (_TTS_IMPORT_ERROR and str(_TTS_IMPORT_ERROR)) or None,
        }

    async def _ensure_ready(self):
        if self._force_legacy_fallback():
            if self._fallback_tts_bin:
                self._last_error = "legacy_fallback_tts"
                return
            raise RuntimeError("legacy_fallback_tts_unavailable")
        if self._force_external_backend():
            if self._external_backend.is_configured:
                async with self._load_lock:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self._external_backend._ensure_started_sync)
                return
            raise RuntimeError("external_tts_unavailable")
        if HAS_TTS and self._allow_inprocess_xtts() and self._model is not None:
            return
        if HAS_TTS and self._allow_inprocess_xtts():
            async with self._load_lock:
                if self._model is not None:
                    return
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._load_model)
            return
        if self._external_backend.is_configured:
            async with self._load_lock:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._external_backend._ensure_started_sync)
            return
        if self._fallback_tts_bin:
            self._last_error = "legacy_fallback_tts"
            return
        raise RuntimeError(
            "No supported TTS backend is installed. Install the 'TTS' package in a "
            "Python 3.9-3.11 environment, configure TTS_PYTHON_PATH for the XTTS helper, "
            "or explicitly enable TWIN_ALLOW_LEGACY_FALLBACK_TTS=1. "
            f"Import error: {_TTS_IMPORT_ERROR}"
        )

    def _load_model(self):
        assert HAS_TTS, "TTS library missing"
        logger.info(f"[speech] Loading XTTS model '{self.model_name}' on {self.device}")

        manager = ModelManager()
        model_dir = os.path.join(
            get_user_data_dir("tts"), self.model_name.replace("/", "--")
        )
        if not os.path.isdir(model_dir):
            try:
                manager.download_model(self.model_name, progress_bar=False)
            except TypeError:
                # Older TTS versions don't accept progress_bar arg; retry without it.
                manager.download_model(self.model_name)
            except EOFError as exc:
                raise RuntimeError(
                    "Coqui TTS download requires accepting the license terms. "
                    "Set COQUI_TOS_AGREED=1 in the environment."
                ) from exc

        config_path = os.path.join(model_dir, "config.json")
        config = XttsConfig()
        config.load_json(config_path)
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=model_dir, use_deepspeed=False)
        try:
            model.to(self.device)
        except Exception as exc:
            # If the GPU is saturated (common on multi-service boxes), prefer a slow but
            # functional CPU fallback rather than crashing the entire speech path.
            oom_types = tuple(
                t
                for t in (
                    getattr(getattr(torch, "cuda", None), "OutOfMemoryError", None),
                    RuntimeError,  # some stacks wrap OOMs as RuntimeError
                )
                if t is not None
            )
            msg = str(exc).lower()
            is_cuda = bool(self.device) and str(self.device).startswith("cuda")
            looks_like_oom = "out of memory" in msg or "cuda out of memory" in msg
            if is_cuda and isinstance(exc, oom_types) and looks_like_oom:
                try:
                    if torch is not None and getattr(torch, "cuda", None) is not None:
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                logger.error(
                    f"[speech] CUDA OOM while loading XTTS on {self.device}; "
                    "DISABLING TTS to prevent system OOM (CPU fallback removed). "
                    "Free GPU VRAM or use remote TTS instead."
                )
                self._last_error = "cuda_oom_tts_disabled"
                self._model = None
                self._config = None
                self._conditioning = None
                return  # Bail out — no TTS is better than crashing the system
            else:
                raise

        self._model = model
        self._config = config
        self._conditioning = self._build_conditioning(model)
        self._last_error = None
        logger.info("[speech] XTTS model ready")

    def _build_conditioning(self, model: Xtts) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.speaker_sample and os.path.isfile(self.speaker_sample):
            logger.info(f"[speech] Using custom speaker sample at {self.speaker_sample}")
            gpt_latent, speaker_embedding = model.get_conditioning_latents(
                audio_path=self.speaker_sample,
                gpt_cond_len=36,
                gpt_cond_chunk_len=12,
                load_sr=22050,
            )
            return gpt_latent.to(self.device), speaker_embedding.to(self.device)

        speaker_name = self.speaker_name or "default"
        speaker_manager = getattr(model, "speaker_manager", None)
        if speaker_manager:
            speakers = getattr(speaker_manager, "speakers", None)
            if speakers and speaker_name in speakers:
                entry = speakers[speaker_name]
                gpt = entry.get("gpt_cond_latent")
                speaker = entry.get("speaker_embedding")
                if gpt is not None and speaker is not None:
                    gpt_tensor = torch.tensor(gpt, device=self.device)
                    spk_tensor = torch.tensor(speaker, device=self.device)
                    logger.info(f"[speech] Using built-in XTTS speaker '{speaker_name}'")
                    return gpt_tensor, spk_tensor

        raise RuntimeError(
            "No speaker reference available for XTTS streaming. Provide "
            "TTS_SPEAKER_WAV or set TTS_VOICE_NAME to a speaker bundled with "
            "the model."
        )

    async def stream_text(self, text: str) -> AsyncIterator[np.ndarray]:
        if not text.strip():
            return

        await self._ensure_ready()
        if self._force_legacy_fallback():
            async for chunk in self._stream_fallback_text(text):
                yield chunk
            return
        if (not HAS_TTS or self._force_external_backend()) and self._external_backend.is_configured:
            loop = asyncio.get_running_loop()
            audio, sample_rate = await loop.run_in_executor(
                None,
                self._external_backend.synthesize_sync,
                text,
            )
            if audio.size == 0:
                return
            chunk_samples = max(
                1,
                int((FALLBACK_TTS_CHUNK_MS / 1000.0) * float(sample_rate or FALLBACK_TTS_SAMPLE_RATE)),
            )
            for idx in range(0, int(audio.size), chunk_samples):
                chunk = audio[idx : idx + chunk_samples]
                if chunk.size:
                    yield chunk.astype(np.float32, copy=False)
            return
        if not HAS_TTS and self._fallback_tts_bin:
            async for chunk in self._stream_fallback_text(text):
                yield chunk
            return
        assert self._model is not None
        assert self._conditioning is not None

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=16)

        def _enqueue_from_worker(item) -> None:
            asyncio.run_coroutine_threadsafe(queue.put(item), loop).result()

        def _synthesis_worker():
            try:
                generator = self._model.inference_stream(
                    text=text,
                    language=self.language,
                    gpt_cond_latent=self._conditioning[0],
                    speaker_embedding=self._conditioning[1],
                    stream_chunk_size=self.chunk_size,
                )
                for chunk in generator:
                    if chunk is None:
                        continue
                    _enqueue_from_worker(chunk.detach().cpu().numpy())
            except Exception as exc:  # pragma: no cover - run_in_executor
                _enqueue_from_worker(exc)
            finally:
                _enqueue_from_worker(None)

        loop.run_in_executor(None, _synthesis_worker)

        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            yield item  # type: ignore[return-value]

    async def _stream_fallback_text(self, text: str) -> AsyncIterator[np.ndarray]:
        loop = asyncio.get_running_loop()
        audio = await loop.run_in_executor(None, self._synthesize_fallback_audio, text)
        if audio.size == 0:
            return
        chunk_samples = max(
            1,
            int((FALLBACK_TTS_CHUNK_MS / 1000.0) * float(FALLBACK_TTS_SAMPLE_RATE)),
        )
        for idx in range(0, int(audio.size), chunk_samples):
            chunk = audio[idx : idx + chunk_samples]
            if chunk.size:
                yield chunk.astype(np.float32, copy=False)

    def _synthesize_fallback_audio(self, text: str) -> np.ndarray:
        tts_bin = self._fallback_tts_bin
        if not tts_bin:
            raise RuntimeError("fallback_tts_unavailable")
        speak_cmd = [
            tts_bin,
            "--stdout",
            "-s",
            str(FALLBACK_TTS_RATE_WPM),
        ]
        if self._fallback_voice:
            speak_cmd += ["-v", self._fallback_voice]
        speak_cmd.append(text)
        speech = subprocess.run(
            speak_cmd,
            check=True,
            capture_output=True,
        )
        convert = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                "pipe:0",
                "-f",
                "f32le",
                "-ar",
                str(FALLBACK_TTS_SAMPLE_RATE),
                "-ac",
                "1",
                "pipe:1",
            ],
            input=speech.stdout,
            check=True,
            capture_output=True,
        )
        pcm = np.frombuffer(convert.stdout, dtype=np.float32)
        if pcm.size == 0:
            return np.zeros(0, dtype=np.float32)
        return np.clip(pcm, -1.0, 1.0).astype(np.float32, copy=False)


class SpeechOrchestrator:
    """High-level helper that ties the TTS engine to the websocket hub."""

    def __init__(
        self,
        engine: Optional[StreamingTTSEngine],
        hub: Optional[SpeechStreamHub],
        enabled: bool = True,
        dtype: str = "int16",
    ):
        self.engine = engine
        self.hub = hub
        self.enabled = enabled
        self.dtype = np.dtype(dtype)
        self._room_locks: Dict[str, asyncio.Lock] = {}

    def _pcm_bytes_per_second(self) -> int:
        if not self.hub:
            return 0
        return (
            int(self.hub.sample_rate)
            * max(1, int(self.hub.channels))
            * int(self.dtype.itemsize)
        )

    def _pcm_frame_bytes(self) -> int:
        if not self.hub:
            return 0
        channels = max(1, int(self.hub.channels))
        frame_samples = max(1, int(float(self.hub.sample_rate) * PCM_STREAM_FRAME_SECONDS))
        return frame_samples * channels * int(self.dtype.itemsize)

    async def _stream_pcm_realtime(self, room: str, pcm: bytes) -> None:
        if not pcm or not self.hub:
            return
        bytes_per_second = self._pcm_bytes_per_second()
        frame_bytes = self._pcm_frame_bytes()
        if bytes_per_second <= 0 or frame_bytes <= 0:
            await self.hub.broadcast_audio(room, pcm)
            return

        loop = asyncio.get_running_loop()
        started = loop.time()
        emitted_duration_s = 0.0
        for idx in range(0, len(pcm), frame_bytes):
            frame = pcm[idx : idx + frame_bytes]
            if not frame:
                continue
            await self.hub.broadcast_audio(room, frame)
            emitted_duration_s += len(frame) / float(bytes_per_second)
            sleep_s = (started + emitted_duration_s) - loop.time()
            if sleep_s > 0:
                await asyncio.sleep(sleep_s)

    async def speak(
        self,
        *,
        text: str,
        room: str,
        metadata: Optional[Dict] = None,
        allow_loopback: bool = False,
    ) -> bool:
        if not self.enabled:
            logger.debug("[speech] Streaming disabled")
            return False
        if not self.engine or not self.hub:
            logger.debug("[speech] Engine or hub missing; skipping speech")
            return False
        if not text.strip():
            logger.debug("[speech] Empty speech text; nothing to play")
            return False
        if self.hub.client_count(room) == 0:
            logger.info(f"[speech] No clients listening for room '{room}'")
            return False

        metadata = metadata or {}
        stream_id = metadata.get("stream_id") or str(uuid.uuid4())
        tts_chunks = _prepare_loopback_playback_chunks(text) if allow_loopback else [text]
        tts_text = " ".join(chunk.strip() for chunk in tts_chunks if chunk and chunk.strip()).strip()
        lock = self._room_locks.get(room)
        if lock is None:
            lock = asyncio.Lock()
            self._room_locks[room] = lock

        async with lock:
            if not allow_loopback:
                # Set noise suppression to prevent feedback loop from TTS audio.
                await set_noise_suppression(room, NOISE_SUPPRESSION_DURATION + 5.0)
                # Record TTS output for LLM echo detection.
                await record_tts_output(room, tts_text)
            
            await self.hub.broadcast_control(
                room,
                {
                    "type": "start",
                    "stream_id": stream_id,
                    "room": room,
                    "meta": metadata,
                },
            )

            try:
                for idx, tts_chunk in enumerate(tts_chunks):
                    if allow_loopback:
                        pre_roll = self._silence_pcm(LOOPBACK_PRE_ROLL_SECONDS)
                        if pre_roll:
                            await self._stream_pcm_realtime(room, pre_roll)
                    async for chunk in self.engine.stream_text(tts_chunk):
                        pcm = self._to_pcm(chunk, gain=LOOPBACK_GAIN if allow_loopback else 1.0)
                        if pcm:
                            await self._stream_pcm_realtime(room, pcm)
                        if not allow_loopback:
                            # Keep extending suppression while speaking.
                            await set_noise_suppression(room, NOISE_SUPPRESSION_DURATION + 2.0)
                    if allow_loopback and idx < len(tts_chunks) - 1:
                        gap = self._silence_pcm(LOOPBACK_BETWEEN_CHUNKS_SECONDS)
                        if gap:
                            await self._stream_pcm_realtime(room, gap)
            except Exception as exc:
                logger.error(f"[speech] Streaming failed for room '{room}': {exc}", exc_info=True)
                await self.hub.broadcast_control(
                    room,
                    {
                        "type": "error",
                        "stream_id": stream_id,
                        "room": room,
                        "message": str(exc),
                    },
                )
                if not allow_loopback:
                    # Still set suppression after error to prevent immediate feedback.
                    await set_noise_suppression(room, NOISE_SUPPRESSION_DURATION)
                return False
            finally:
                await self.hub.broadcast_control(
                    room,
                    {
                        "type": "end",
                        "stream_id": stream_id,
                        "room": room,
                    },
                )
                if not allow_loopback:
                    # Set final suppression window after speech ends.
                    await set_noise_suppression(room, NOISE_SUPPRESSION_DURATION)
                    logger.debug(f"[speech] Noise suppression set for room '{room}' for {NOISE_SUPPRESSION_DURATION}s")

        return True

    async def play_notification(
        self,
        *,
        room: str,
        kind: str = "wake",
        metadata: Optional[Dict] = None,
    ) -> bool:
        if not self.hub:
            logger.debug("[speech] Hub missing; skipping notification")
            return False
        if self.hub.client_count(room) == 0:
            logger.info(f"[speech] No clients listening for room '{room}'")
            return False

        metadata = dict(metadata or {})
        metadata.setdefault("type", "notification")
        metadata.setdefault("kind", kind)
        stream_id = metadata.get("stream_id") or f"notification-{uuid.uuid4()}"
        lock = self._room_locks.get(room)
        if lock is None:
            lock = asyncio.Lock()
            self._room_locks[room] = lock

        async with lock:
            await set_noise_suppression(room, 1.5)
            await self.hub.broadcast_control(
                room,
                {
                    "type": "start",
                    "stream_id": stream_id,
                    "room": room,
                    "meta": metadata,
                },
            )
            try:
                pcm = self._notification_pcm(kind)
                await self._stream_pcm_realtime(room, pcm)
            except Exception as exc:
                logger.error(
                    f"[speech] Notification streaming failed for room '{room}': {exc}",
                    exc_info=True,
                )
                await self.hub.broadcast_control(
                    room,
                    {
                        "type": "error",
                        "stream_id": stream_id,
                        "room": room,
                        "message": str(exc),
                    },
                )
                await set_noise_suppression(room, 1.0)
                return False
            finally:
                await self.hub.broadcast_control(
                    room,
                    {
                        "type": "end",
                        "stream_id": stream_id,
                        "room": room,
                    },
                )
                await set_noise_suppression(room, 1.0)

        return True

    def _to_pcm(self, chunk: np.ndarray, *, gain: float = 1.0) -> bytes:
        if chunk.size == 0:
            return b""
        mono = chunk
        if chunk.ndim > 1:
            mono = np.mean(chunk, axis=1)
        normalized = np.clip(mono * float(gain), -1.0, 1.0)
        pcm = (normalized * np.iinfo(self.dtype).max).astype(self.dtype)
        return pcm.tobytes()

    def _silence_pcm(self, duration_s: float) -> bytes:
        if duration_s <= 0 or not self.hub:
            return b""
        total_samples = max(1, int(float(duration_s) * int(self.hub.sample_rate)))
        shape = (total_samples, max(1, int(self.hub.channels)))
        silence = np.zeros(shape, dtype=self.dtype)
        return silence.tobytes()

    def _notification_pcm(self, kind: str) -> bytes:
        sample_rate = int(self.hub.sample_rate if self.hub else 24000)
        tone = self._notification_wave(kind, sample_rate=sample_rate)
        return self._to_pcm(tone)

    def _notification_wave(self, kind: str, *, sample_rate: int) -> np.ndarray:
        kind_norm = str(kind or "wake").strip().lower()
        if kind_norm == "sleep":
            notes = [(784.0, 0.08, 0.18), (587.33, 0.12, 0.14)]
            gap_s = 0.012
        else:
            notes = [(659.25, 0.08, 0.16), (987.77, 0.12, 0.20)]
            gap_s = 0.015

        parts: list[np.ndarray] = []
        for idx, (freq, duration_s, amplitude) in enumerate(notes):
            total = max(1, int(sample_rate * duration_s))
            t = np.linspace(0, duration_s, total, endpoint=False, dtype=np.float32)
            wave = amplitude * np.sin((2.0 * np.pi * freq * t).astype(np.float32))
            fade = max(1, int(total * 0.18))
            envelope = np.ones(total, dtype=np.float32)
            envelope[:fade] = np.linspace(0.0, 1.0, fade, endpoint=True, dtype=np.float32)
            envelope[-fade:] = np.linspace(1.0, 0.0, fade, endpoint=True, dtype=np.float32)
            parts.append((wave * envelope).astype(np.float32))
            if idx != len(notes) - 1 and gap_s > 0:
                parts.append(np.zeros(max(1, int(sample_rate * gap_s)), dtype=np.float32))
        if not parts:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(parts).astype(np.float32)
