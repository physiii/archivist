from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import indexing_service


def test_backup_linked_schedule_snapshot_uses_backup_schedule(monkeypatch):
    now = datetime(2026, 3, 20, 1, 15, tzinfo=timezone.utc)
    last_triggered = datetime(2026, 3, 19, 2, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(
        indexing_service,
        "get_schedule_config",
        lambda: {
            "enabled": True,
            "time_of_day": "02:00",
            "timezone": "utc",
            "next_run_at": None,
            "last_triggered_at": None,
        },
    )
    monkeypatch.setattr(indexing_service, "_schedule_loaded", True)
    indexing_service._schedule.last_triggered_at = last_triggered

    snapshot = indexing_service._backup_linked_schedule_snapshot(now)

    assert snapshot["source"] == "backup"
    assert snapshot["enabled"] is True
    assert snapshot["time_of_day"] == "02:00"
    assert snapshot["timezone"] == "utc"
    assert snapshot["next_run_at"] == "2026-03-20T02:00:00+00:00"
    assert snapshot["last_triggered_at"] == "2026-03-19T02:00:00+00:00"


def test_schedule_worker_triggers_indexing_for_due_backup_slot(monkeypatch):
    now = datetime.now(timezone.utc)
    time_of_day = (now - timedelta(minutes=1)).strftime("%H:%M")
    calls: list[str] = []

    class OneShotStop:
        def __init__(self) -> None:
            self._done = False

        def is_set(self) -> bool:
            return self._done

        def wait(self, _timeout: float) -> bool:
            self._done = True
            return True

    monkeypatch.setattr(indexing_service, "_scheduler_stop", OneShotStop())
    monkeypatch.setattr(
        indexing_service,
        "get_schedule_config",
        lambda: {
            "enabled": True,
            "time_of_day": time_of_day,
            "timezone": "utc",
            "next_run_at": None,
            "last_triggered_at": None,
        },
    )
    monkeypatch.setattr(indexing_service, "_save_schedule_state", lambda: None)
    monkeypatch.setattr(indexing_service, "_schedule_loaded", True)
    monkeypatch.setattr(indexing_service, "start_indexing", lambda: calls.append("started"))
    indexing_service._schedule.last_triggered_at = None

    indexing_service._schedule_worker()

    assert calls == ["started"]
    assert indexing_service._schedule.last_triggered_at is not None
