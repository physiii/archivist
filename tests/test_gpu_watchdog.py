"""Tests for gpu_watchdog module."""

import signal
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gpu_watchdog


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level state between tests."""
    gpu_watchdog._state = "unknown"
    gpu_watchdog._last_check_ts = 0.0
    gpu_watchdog._last_ok_ts = 0.0
    gpu_watchdog._lost_since_ts = 0.0
    gpu_watchdog._last_alert_ts = 0.0
    gpu_watchdog._last_error = None
    gpu_watchdog._device_name = None
    gpu_watchdog._check_count = 0
    gpu_watchdog._loss_count = 0
    gpu_watchdog._exit_triggered = False
    gpu_watchdog.GPU_WATCHDOG_EXIT_ON_LOSS = True
    gpu_watchdog.GPU_WATCHDOG_EXIT_AFTER_S = 180.0
    yield
    gpu_watchdog.stop(timeout=1)


class TestProbe:
    def test_probe_reports_no_torch(self):
        with patch.dict(sys.modules, {"torch": None}):
            ok, name, err = gpu_watchdog._probe_cuda()
        assert not ok
        assert "not installed" in (err or "") or "None" in (err or "")

    @patch("gpu_watchdog.os.getenv", return_value="0")
    def test_probe_cuda_unavailable(self, _):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict(sys.modules, {"torch": mock_torch}):
            ok, name, err = gpu_watchdog._probe_cuda()
        assert not ok
        assert "False" in (err or "")

    @patch("gpu_watchdog.os.getenv", return_value="0")
    def test_probe_cuda_available(self, _):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "NVIDIA RTX 4090"
        mock_torch.zeros.return_value = MagicMock()
        with patch.dict(sys.modules, {"torch": mock_torch}):
            ok, name, err = gpu_watchdog._probe_cuda()
        assert ok
        assert name == "NVIDIA RTX 4090"
        assert err is None


class TestStateTransitions:
    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(True, "RTX 4090", None))
    def test_unknown_to_ok(self, _probe, mock_notif):
        gpu_watchdog._state = "unknown"
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        assert gpu_watchdog._state == "ok"
        assert gpu_watchdog._device_name == "RTX 4090"
        assert gpu_watchdog._check_count > 0

    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(False, None, "device gone"))
    def test_ok_to_lost_sends_alert(self, _probe, mock_notif):
        gpu_watchdog._state = "ok"
        gpu_watchdog._last_ok_ts = time.time()
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        assert gpu_watchdog._state == "lost"
        assert gpu_watchdog._loss_count >= 1
        mock_notif.send_all.assert_called()
        call_args = mock_notif.send_all.call_args
        assert "LOST" in call_args[0][0]
        assert call_args[1].get("severity") == "error" or (len(call_args[0]) >= 3 and call_args[0][2] == "error")

    @patch("gpu_watchdog.notifications")
    def test_lost_to_recovered_sends_alert(self, mock_notif):
        gpu_watchdog._state = "lost"
        gpu_watchdog._lost_since_ts = time.time() - 60
        gpu_watchdog._loss_count = 1
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        with patch("gpu_watchdog._probe_cuda", return_value=(True, "RTX 4090", None)):
            gpu_watchdog.start()
            time.sleep(0.3)
            gpu_watchdog.stop()
        assert gpu_watchdog._state == "ok"
        mock_notif.send_all.assert_called()
        titles = [c[0][0] for c in mock_notif.send_all.call_args_list]
        assert any("RECOVERED" in t for t in titles)

    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(False, None, "still gone"))
    def test_repeat_alert_after_interval(self, _probe, mock_notif):
        gpu_watchdog._state = "lost"
        gpu_watchdog._lost_since_ts = time.time() - 3600
        gpu_watchdog._last_alert_ts = time.time() - 3600
        gpu_watchdog._loss_count = 1
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.GPU_WATCHDOG_REPEAT_S = 0.01
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        titles = [c[0][0] for c in mock_notif.send_all.call_args_list]
        assert any("STILL LOST" in t for t in titles)


class TestAutoRecovery:
    @patch("gpu_watchdog.os.kill")
    @patch("gpu_watchdog.notifications")
    def test_trigger_signals_pid1_and_is_idempotent(self, mock_notif, mock_kill):
        gpu_watchdog._exit_triggered = False
        gpu_watchdog._trigger_container_restart("device gone", 200.0)
        mock_kill.assert_called_once_with(1, signal.SIGTERM)
        assert gpu_watchdog._exit_triggered is True
        # A second call must NOT signal again (at-most-once per episode).
        gpu_watchdog._trigger_container_restart("device gone", 260.0)
        mock_kill.assert_called_once()
        titles = [c[0][0] for c in mock_notif.send_all.call_args_list]
        assert any("restarting container" in t.lower() for t in titles)

    @patch("gpu_watchdog.os.kill")
    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(False, None, "device gone"))
    def test_sustained_loss_after_prior_health_restarts(self, _probe, mock_notif, mock_kill):
        gpu_watchdog._state = "lost"
        gpu_watchdog._last_ok_ts = time.time() - 100      # was healthy this session
        gpu_watchdog._lost_since_ts = time.time() - 100   # lost long enough
        gpu_watchdog._last_alert_ts = time.time()
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.GPU_WATCHDOG_EXIT_ON_LOSS = True
        gpu_watchdog.GPU_WATCHDOG_EXIT_AFTER_S = 0.01
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        mock_kill.assert_called_once_with(1, signal.SIGTERM)

    @patch("gpu_watchdog.os.kill")
    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(False, None, "never came up"))
    def test_loss_without_prior_health_does_not_restart(self, _probe, mock_notif, mock_kill):
        # GPU absent from boot (never healthy this session) must NOT crash-loop.
        gpu_watchdog._state = "unknown"
        gpu_watchdog._last_ok_ts = 0.0
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.GPU_WATCHDOG_EXIT_ON_LOSS = True
        gpu_watchdog.GPU_WATCHDOG_EXIT_AFTER_S = 0.01
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        mock_kill.assert_not_called()

    @patch("gpu_watchdog.os.kill")
    @patch("gpu_watchdog.notifications")
    @patch("gpu_watchdog._probe_cuda", return_value=(False, None, "device gone"))
    def test_disabled_does_not_restart(self, _probe, mock_notif, mock_kill):
        gpu_watchdog._state = "lost"
        gpu_watchdog._last_ok_ts = time.time() - 100
        gpu_watchdog._lost_since_ts = time.time() - 100
        gpu_watchdog._last_alert_ts = time.time()
        gpu_watchdog.GPU_WATCHDOG_STARTUP_GRACE_S = 0
        gpu_watchdog.GPU_WATCHDOG_INTERVAL_S = 0.05
        gpu_watchdog.GPU_WATCHDOG_EXIT_ON_LOSS = False
        gpu_watchdog.GPU_WATCHDOG_EXIT_AFTER_S = 0.01
        gpu_watchdog.start()
        time.sleep(0.3)
        gpu_watchdog.stop()
        mock_kill.assert_not_called()


class TestPublicAPI:
    def test_gpu_ok_reflects_state(self):
        gpu_watchdog._state = "ok"
        assert gpu_watchdog.gpu_ok() is True
        gpu_watchdog._state = "lost"
        assert gpu_watchdog.gpu_ok() is False
        gpu_watchdog._state = "unknown"
        assert gpu_watchdog.gpu_ok() is False

    def test_status_returns_dict(self):
        s = gpu_watchdog.status()
        assert isinstance(s, dict)
        assert "state" in s
        assert "interval_s" in s
        assert "loss_count" in s
