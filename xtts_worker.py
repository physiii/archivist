#!/usr/bin/env python3
"""
External XTTS worker for Twin.

This process runs under the dedicated TTS virtualenv and keeps the XTTS model
warm across requests. It communicates over newline-delimited JSON on stdio.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np


def _configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=os.getenv("ARCHIVIST_XTTS_WORKER_LOG_LEVEL", "INFO").upper(),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s [xtts-worker] %(message)s",
    )
    return logging.getLogger("archivist.xtts_worker")


logger = _configure_logging()


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _patch_transformers_compat() -> None:
    import transformers
    from transformers.generation.beam_constraints import (
        DisjunctiveConstraint,
        PhrasalConstraint,
    )
    from transformers.generation.beam_search import (
        BeamSearchScorer,
        ConstrainedBeamSearchScorer,
    )
    from transformers.generation.configuration_utils import GenerationConfig
    from transformers.generation.logits_process import LogitsProcessorList
    from transformers.generation.stopping_criteria import StoppingCriteriaList
    from transformers.generation.utils import GenerationMixin
    from transformers.modeling_utils import PreTrainedModel

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

    # Prime XTTS stream support after the compatibility exports are in place.
    from TTS.tts.layers.xtts import stream_generator  # noqa: F401
    from TTS.tts.layers.xtts.gpt_inference import GPT2InferenceModel

    if GenerationMixin not in GPT2InferenceModel.__mro__:
        GPT2InferenceModel.__bases__ = (GenerationMixin,) + GPT2InferenceModel.__bases__
    if not hasattr(GPT2InferenceModel, "_validate_model_class"):
        GPT2InferenceModel._validate_model_class = lambda self: None


def _import_tts_modules():
    os.environ.setdefault("COQUI_TOS_AGREED", "1")
    os.environ.setdefault("COQUI_LANG", "en")

    _patch_transformers_compat()

    import torch
    from torch.serialization import add_safe_globals
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts, XttsArgs, XttsAudioConfig
    from TTS.utils.generic_utils import get_user_data_dir
    from TTS.utils.manage import ModelManager

    try:
        from TTS.config.shared_configs import BaseDatasetConfig
    except Exception:
        BaseDatasetConfig = None

    safe_classes = [
        cls
        for cls in (XttsConfig, XttsAudioConfig, XttsArgs, BaseDatasetConfig)
        if cls is not None
    ]
    if safe_classes:
        add_safe_globals(safe_classes)

    return {
        "torch": torch,
        "XttsConfig": XttsConfig,
        "Xtts": Xtts,
        "ModelManager": ModelManager,
        "get_user_data_dir": get_user_data_dir,
    }


def _build_conditioning(model, device, *, speaker_name: str, speaker_sample: str | None):
    if speaker_sample and os.path.isfile(speaker_sample):
        gpt_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=speaker_sample,
            gpt_cond_len=36,
            gpt_cond_chunk_len=12,
            load_sr=22050,
        )
        return gpt_latent.to(device), speaker_embedding.to(device)

    speakers = getattr(getattr(model, "speaker_manager", None), "speakers", None) or {}
    entry = speakers.get(speaker_name)
    if not isinstance(entry, dict):
        raise RuntimeError(f"unknown_speaker:{speaker_name}")

    import torch

    gpt = entry.get("gpt_cond_latent")
    speaker = entry.get("speaker_embedding")
    if gpt is None or speaker is None:
        raise RuntimeError(f"missing_speaker_conditioning:{speaker_name}")
    gpt_tensor = torch.tensor(gpt, device=device)
    speaker_tensor = torch.tensor(speaker, device=device)
    return gpt_tensor, speaker_tensor


class XTTSWorker:
    def __init__(self, *, model_name: str, language: str, speaker_name: str, speaker_sample: str | None, device: str):
        modules = _import_tts_modules()
        self.torch = modules["torch"]
        self.XttsConfig = modules["XttsConfig"]
        self.Xtts = modules["Xtts"]
        self.ModelManager = modules["ModelManager"]
        self.get_user_data_dir = modules["get_user_data_dir"]
        self.model_name = model_name
        self.language = language
        self.speaker_name = speaker_name
        self.speaker_sample = speaker_sample
        self.device = str(device or "cpu")
        self.model = None
        self.sample_rate = 24000
        self.conditioning = None

    def _resolve_device(self) -> str:
        requested = str(self.device or "cpu").strip().lower() or "cpu"
        if requested.startswith("cuda"):
            try:
                if not self.torch.cuda.is_available():
                    logger.warning("Requested CUDA device %s but CUDA is unavailable; using CPU", requested)
                    return "cpu"
            except Exception:
                logger.warning("Could not validate CUDA availability for %s; using CPU", requested)
                return "cpu"
        return requested

    def load(self) -> None:
        self.device = self._resolve_device()
        model_dir = Path(self.get_user_data_dir("tts")) / self.model_name.replace("/", "--")
        if not model_dir.exists():
            manager = self.ModelManager()
            try:
                manager.download_model(self.model_name, progress_bar=False)
            except TypeError:
                manager.download_model(self.model_name)

        config_path = model_dir / "config.json"
        config = self.XttsConfig()
        config.load_json(str(config_path))
        model = self.Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=str(model_dir), use_deepspeed=False)
        model.to(self.device)
        self.model = model
        self.sample_rate = int(getattr(getattr(config, "audio", None), "sample_rate", 24000) or 24000)
        self.conditioning = _build_conditioning(
            model,
            self.device,
            speaker_name=self.speaker_name,
            speaker_sample=self.speaker_sample,
        )

    def synthesize(self, text: str) -> np.ndarray:
        if self.model is None or self.conditioning is None:
            raise RuntimeError("worker_not_ready")
        result = self.model.inference(
            text=text,
            language=self.language,
            gpt_cond_latent=self.conditioning[0],
            speaker_embedding=self.conditioning[1],
            temperature=float(os.getenv("TWIN_XTTS_TEMPERATURE", "0.65")),
            length_penalty=float(os.getenv("TWIN_XTTS_LENGTH_PENALTY", "1.0")),
            repetition_penalty=float(os.getenv("TWIN_XTTS_REPETITION_PENALTY", "2.0")),
            top_k=int(os.getenv("TWIN_XTTS_TOP_K", "50")),
            top_p=float(os.getenv("TWIN_XTTS_TOP_P", "0.8")),
            enable_text_splitting=False,
        )
        wav_data = result.get("wav")
        if wav_data is None:
            wav_data = []
        wav = np.asarray(wav_data, dtype=np.float32).reshape(-1)
        if wav.size == 0:
            return np.zeros((0,), dtype=np.float32)
        return np.clip(wav, -1.0, 1.0).astype(np.float32, copy=False)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Twin XTTS helper")
    parser.add_argument("--model", required=True)
    parser.add_argument("--language", default="en")
    parser.add_argument("--speaker-name", default="Ana Florence")
    parser.add_argument("--speaker-sample", default="")
    parser.add_argument("--device", default="cuda")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        worker = XTTSWorker(
            model_name=args.model,
            language=args.language,
            speaker_name=args.speaker_name,
            speaker_sample=(args.speaker_sample or "").strip() or None,
            device=args.device,
        )
        worker.load()
        _emit(
            {
                "event": "ready",
                "ok": True,
                "backend": "xtts_external",
                "model": args.model,
                "language": args.language,
                "speaker_name": args.speaker_name,
                "device": worker.device,
                "sample_rate": worker.sample_rate,
            }
        )
    except Exception as exc:
        logger.exception("XTTS helper failed to start")
        _emit(
            {
                "event": "ready",
                "ok": False,
                "backend": "xtts_external",
                "error": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
        )
        return 1

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except Exception:
            _emit({"ok": False, "error": "invalid_json"})
            continue

        req_type = str(request.get("type") or "").strip().lower()
        if req_type == "status":
            _emit(
                {
                    "ok": True,
                    "backend": "xtts_external",
                    "model": args.model,
                    "language": args.language,
                    "speaker_name": args.speaker_name,
                    "device": worker.device,
                    "sample_rate": worker.sample_rate,
                    "ready": worker.model is not None,
                }
            )
            continue
        if req_type == "shutdown":
            _emit({"ok": True, "shutdown": True})
            break
        if req_type != "synthesize":
            _emit({"ok": False, "error": f"unknown_request:{req_type or 'missing'}"})
            continue

        text = str(request.get("text") or "").strip()
        if not text:
            _emit({"ok": False, "error": "empty_text"})
            continue

        try:
            wav = worker.synthesize(text)
            audio_b64 = base64.b64encode(wav.astype("<f4", copy=False).tobytes()).decode("ascii")
            _emit(
                {
                    "ok": True,
                    "backend": "xtts_external",
                    "model": args.model,
                    "language": args.language,
                    "speaker_name": args.speaker_name,
                    "device": worker.device,
                    "sample_rate": worker.sample_rate,
                    "audio_b64": audio_b64,
                }
            )
        except Exception as exc:
            logger.exception("XTTS helper synthesis failed")
            _emit(
                {
                    "ok": False,
                    "backend": "xtts_external",
                    "error": str(exc),
                    "traceback": traceback.format_exc(limit=8),
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
