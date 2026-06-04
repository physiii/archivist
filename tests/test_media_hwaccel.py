"""Tests for GPU-accelerated decode (NVDEC) with software fallback, and the
batch-media priority gate that yields to real-time transcription."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import media.filtering as filtering
import media.pipeline as pipeline


def _completed(rc):
    m = MagicMock()
    m.returncode = rc
    m.stderr = ""
    return m


class TestHwaccel:
    def setup_method(self):
        filtering._hwaccel_disabled = False
        filtering._hwaccel_failures = 0
        filtering.FFMPEG_HWACCEL = "cuda"
        filtering._HWACCEL_MAX_FAILURES = 3

    def test_hwaccel_args_enabled(self):
        assert filtering._hwaccel_args() == ["-hwaccel", "cuda"]

    def test_hwaccel_args_disabled_when_empty(self):
        filtering.FFMPEG_HWACCEL = ""
        assert filtering._hwaccel_args() == []

    def test_decode_tries_gpu_then_falls_back_to_software(self):
        calls = []

        def build(hw):
            calls.append(list(hw))
            return ["ffmpeg", *hw, "-i", "x", "-f", "null", "-"]

        with patch.object(filtering.subprocess, "run", side_effect=[_completed(1), _completed(0)]) as run:
            res = filtering._run_ffmpeg_decode(build, timeout=10)

        assert calls == [["-hwaccel", "cuda"], []]  # GPU attempt, then software
        assert res.returncode == 0
        assert run.call_count == 2

    def test_decode_no_fallback_on_gpu_success(self):
        calls = []

        def build(hw):
            calls.append(list(hw))
            return ["ffmpeg", *hw, "-i", "x"]

        with patch.object(filtering.subprocess, "run", side_effect=[_completed(0)]):
            res = filtering._run_ffmpeg_decode(build, timeout=10)

        assert calls == [["-hwaccel", "cuda"]]
        assert res.returncode == 0

    def test_circuit_breaker_disables_hwaccel_after_repeated_failures(self):
        filtering._HWACCEL_MAX_FAILURES = 2
        build = lambda hw: ["ffmpeg", *hw, "-i", "x"]

        with patch.object(filtering.subprocess, "run", return_value=_completed(1)):
            filtering._run_ffmpeg_decode(build, timeout=10)
            assert filtering._hwaccel_disabled is False
            filtering._run_ffmpeg_decode(build, timeout=10)

        assert filtering._hwaccel_disabled is True
        assert filtering._hwaccel_args() == []  # future calls skip the GPU


class TestCapacityGate:
    def test_proceeds_immediately_when_load_low(self):
        with patch.object(pipeline.os, "getloadavg", return_value=(0.1, 0.1, 0.1)), \
             patch.object(pipeline.time, "sleep") as slp:
            pipeline._wait_for_media_capacity()
        slp.assert_not_called()

    def test_defers_until_load_drops(self):
        loads = [(10000.0, 0, 0), (10000.0, 0, 0), (0.1, 0, 0)]
        with patch.object(pipeline, "MEDIA_WATCH_MAX_LOAD_PER_CPU", 1.0), \
             patch.object(pipeline.os, "getloadavg", side_effect=loads), \
             patch.object(pipeline.time, "sleep") as slp:
            pipeline._wait_for_media_capacity()
        assert slp.call_count == 2  # waited through both high-load samples

    def test_gate_disabled_when_ratio_zero(self):
        with patch.object(pipeline, "MEDIA_WATCH_MAX_LOAD_PER_CPU", 0.0), \
             patch.object(pipeline.os, "getloadavg") as gl:
            pipeline._wait_for_media_capacity()
        gl.assert_not_called()
