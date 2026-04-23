import importlib.util
import sys
import threading
import time
import types
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
_REAL_THREAD_START = threading.Thread.start


def _load_module(name: str, relative_path: str):
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def _load_main_with_stubs(module_name: str):
    load_stub = types.ModuleType("load")
    load_stub.load_to_vectorstore = lambda *a, **k: None
    load_stub.load_text_to_vectorstore = lambda *a, **k: {"ok": True}
    load_stub.clear_vectorstore_collection = lambda *a, **k: {"ok": True}
    sys.modules["load"] = load_stub

    search_stub = types.ModuleType("search")
    search_stub.search_vectorstore = lambda *a, **k: []
    sys.modules["search"] = search_stub

    backups_stub = types.ModuleType("backups_service")
    backups_stub.BACKUP_ROOT = "/tmp"
    backups_stub.add_backup_target = lambda *a, **k: None
    backups_stub.delete_backup_target = lambda *a, **k: None
    backups_stub.get_backup_overview = lambda *a, **k: {"status": {"running": False}}
    backups_stub.get_run_logs = lambda *a, **k: []
    backups_stub.list_backup_targets = lambda *a, **k: []
    backups_stub.start_backup = lambda *a, **k: None
    backups_stub.start_scheduler_best_effort = lambda *a, **k: None
    backups_stub.start_target_backup = lambda *a, **k: None
    backups_stub.stop_backup = lambda *a, **k: None
    backups_stub.update_backup_target = lambda *a, **k: None
    backups_stub.update_schedule = lambda *a, **k: None
    sys.modules["backups_service"] = backups_stub

    indexing_stub = types.ModuleType("indexing_service")
    indexing_stub.GOOGLE_ARCHIVE_CONTENT_VERSION = "google_archive_v1"
    indexing_stub.add_indexing_target = lambda *a, **k: None
    indexing_stub.delete_indexing_target = lambda *a, **k: None
    indexing_stub.get_indexing_overview = lambda *a, **k: {"status": {"running": False}}
    indexing_stub.get_indexing_run_logs = lambda *a, **k: []
    indexing_stub.index_google_archive_content = lambda *a, **k: {
        "records_seen": 0,
        "records_indexed": 0,
        "chunks_inserted": 0,
        "errors": [],
    }
    indexing_stub.list_indexing_targets = lambda *a, **k: []
    indexing_stub.scan_indexing_target = lambda *a, **k: {}
    indexing_stub.start_indexing = lambda *a, **k: None
    indexing_stub.start_scheduler_best_effort = lambda *a, **k: None
    indexing_stub.start_target_indexing = lambda *a, **k: None
    indexing_stub.stop_indexing = lambda *a, **k: None
    indexing_stub.update_indexing_target = lambda *a, **k: None
    sys.modules["indexing_service"] = indexing_stub

    movietime_stub = types.ModuleType("movietime_items")
    movietime_stub.search_movietime_items = lambda *a, **k: []
    movietime_stub.upsert_movietime_items = lambda *a, **k: {"ok": True}
    sys.modules["movietime_items"] = movietime_stub

    chat_store_stub = types.ModuleType("chat_store")
    chat_store_stub.add_message = lambda *a, **k: None
    chat_store_stub.create_session = lambda *a, **k: {"id": "session-1"}
    chat_store_stub.delete_session = lambda *a, **k: None
    chat_store_stub.get_session_messages = lambda *a, **k: []
    chat_store_stub.init_db = lambda *a, **k: None
    chat_store_stub.list_sessions = lambda *a, **k: []
    chat_store_stub.update_session_title = lambda *a, **k: None
    sys.modules["chat_store"] = chat_store_stub

    transcription_stub = types.ModuleType("transcription_service")
    transcription_stub.init_transcription_model = lambda *a, **k: None
    transcription_stub.transcribe_audio = lambda *a, **k: {"segments": []}
    sys.modules["transcription_service"] = transcription_stub

    agent_stub = types.ModuleType("agent_integration")
    agent_stub.build_agent_system_message = lambda *a, **k: ""
    agent_stub.console_agent_id = lambda: "archivist-main"
    agent_stub.decode_session_ref = lambda *a, **k: ("archivist-main", "main:web:test@archivist-main")
    agent_stub.default_web_session_key = lambda *a, **k: "main:web:test@archivist-main"
    agent_stub.encode_session_ref = lambda *a, **k: "agent:archivist-main:main:web:test@archivist-main"
    agent_stub.gateway_session_key = lambda *a, **k: "agent:archivist-main:main:web:test@archivist-main"
    agent_stub.host_workspace = lambda: str(REPO_ROOT)
    agent_stub.inspect_agent_runtime = lambda *a, **k: {"available": False, "registered_agents": []}
    agent_stub.load_openclaw_config = lambda *a, **k: ({}, None)
    agent_stub.load_openclaw_messages_from_transcript = lambda *a, **k: []
    agent_stub.load_openclaw_sessions_for_agents = lambda *a, **k: []
    agent_stub.load_team_agents = lambda *a, **k: []
    agent_stub.registered_agent_ids = lambda *a, **k: []
    agent_stub.resolve_gateway_token = lambda: ""
    agent_stub.resolve_gateway_url = lambda: "http://localhost"
    agent_stub.resolve_openclaw_session_file = lambda *a, **k: None
    agent_stub.session_kind = lambda *a, **k: "chat"
    agent_stub.visible_agent_ids = lambda *a, **k: []
    sys.modules["agent_integration"] = agent_stub

    return _load_module(module_name, "main.py")


def _base_lane(lane_id: str) -> dict:
    title = "Personal" if lane_id == "personal" else "Business"
    subtitle = "Archive-driven personal focus" if lane_id == "personal" else "Notes-backed business focus"
    source_label = "Personal archive synthesis" if lane_id == "personal" else "Business notes"
    return {
        "id": lane_id,
        "title": title,
        "subtitle": subtitle,
        "available": True,
        "generatedAt": "2026-04-23T18:55:00+00:00",
        "sourceLabel": source_label,
        "sections": [
            {
                "id": "priorities",
                "title": "Priorities",
                "kind": "priority_table",
                "items": [
                    {
                        "num": "1",
                        "title": f"Archive-backed {title.lower()} focus",
                        "owner": "Andy",
                        "status": "Live",
                        "next_action": "Review the archive-backed lane context.",
                        "detail_md": "Baseline archive-backed focus item.",
                    }
                ],
            }
        ],
    }


def _manual_entry(
    entry_id: str,
    title: str,
    detail_md: str,
    *,
    lane_id: str,
    created_at: str,
    status: str = "Added Apr 23",
    next_action: str | None = None,
) -> dict:
    return {
        "id": entry_id,
        "laneId": lane_id,
        "createdAt": created_at,
        "title": title,
        "status": status,
        "next_action": next_action or detail_md,
        "detail_md": detail_md,
    }


@pytest.fixture
def focus_main(monkeypatch, tmp_path):
    state_dir = tmp_path / "focus-state"
    monkeypatch.setenv("ARCHIVIST_FOCUS_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ARCHIVIST_TEST_REPORTS_DIR", str(tmp_path / "test-reports"))
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)

    main = _load_main_with_stubs(f"archivist_focus_eval_{uuid4().hex}")
    monkeypatch.setattr(threading.Thread, "start", _REAL_THREAD_START)
    snapshot_lane = _base_lane("personal")

    monkeypatch.setattr(main, "_start_personal_focus_sync", lambda *a, **k: False)
    monkeypatch.setattr(main, "_build_work_focus_lane", lambda: _base_lane("work"))
    monkeypatch.setattr(
        main,
        "_focus_personal_source_context",
        lambda: {
            "today": "2026-04-23",
            "fingerprint": "focus-test-fingerprint",
            "archiveFingerprint": "focus-test-archive",
            "generatedAt": "2026-04-23T18:55:00+00:00",
            "lastImportedAt": "2026-04-23T18:55:00+00:00",
        },
    )
    monkeypatch.setattr(main, "_focus_personal_lane_for_response", lambda source_context: snapshot_lane)
    monkeypatch.setattr(main, "_load_personal_focus_snapshot", lambda: {"generatedAt": "2026-04-23T18:55:00+00:00", "lane": snapshot_lane})
    monkeypatch.setattr(
        main,
        "_personal_focus_sync_status",
        lambda source_context, snapshot: {
            "running": False,
            "message": "",
            "startedAt": None,
            "finishedAt": None,
            "lastSuccessfulAt": "2026-04-23T18:55:00+00:00",
            "error": None,
            "stale": False,
            "schedule": {"enabled": True, "time_of_day": "05:30", "timezone": "America/Chicago"},
        },
    )
    monkeypatch.setattr(
        main,
        "_focus_manual_priority_context_payload",
        lambda lane_id: {
            "laneId": lane_id,
            "title": "Personal" if lane_id == "personal" else "Business",
            "subtitle": "Eval lane",
            "context": "Console eval harness",
            "sections": [{"id": "priorities", "title": "Priorities", "sample": "Baseline focus"}],
        },
    )
    return main


def _seed_manual_priorities(main, *, work=None, personal=None) -> None:
    main._save_focus_manual_priorities(
        {
            "work": list(work or []),
            "personal": list(personal or []),
        }
    )


def test_focus_priority_eval_adds_personal_note_when_gateway_is_unavailable(focus_main, monkeypatch):
    monkeypatch.setattr(focus_main, "_focus_call_gateway_json", lambda **kwargs: None)
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Need to confirm Jonas pickup time, finish the bank paperwork, and square away the travel details before Sunday.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert len(payload["entries"]) == 1
    assert "Jonas pickup time" in payload["entries"][0]["detail_md"]

    stored = focus_main._load_focus_manual_priorities()["personal"]
    assert len(stored) == 1
    assert "bank paperwork" in stored[0]["detail_md"]


def test_focus_priority_eval_removes_resolved_personal_item(focus_main, monkeypatch):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "jonas",
                "Confirm Jonas pickup time",
                "Need the exact pickup time from Jonas.",
                lane_id="personal",
                created_at="2026-04-23T10:00:00+00:00",
                next_action="Lock the pickup time today.",
            ),
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Bank paperwork is still open.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Finish the pending forms.",
            ),
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_focus_call_gateway_json",
        lambda **kwargs: {
            "items": [
                {
                    "id": "bank",
                    "title": "Finish bank paperwork",
                    "status": "Still open",
                    "next_action": "Finish the bank paperwork before Sunday.",
                    "detail_md": "Keep this active until the forms are done.",
                }
            ]
        },
    )
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Jonas pickup is resolved. Keep the bank paperwork and drop Jonas from personal focus.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert [entry["title"] for entry in payload["entries"]] == ["Finish bank paperwork"]

    stored = focus_main._load_focus_manual_priorities()["personal"]
    assert [entry["id"] for entry in stored] == ["bank"]
    assert stored[0]["createdAt"] == "2026-04-23T10:05:00+00:00"


def test_focus_priority_eval_modifies_and_reorders_personal_items(focus_main, monkeypatch):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Bank paperwork is still open.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Finish the pending forms.",
            ),
            _manual_entry(
                "travel",
                "Square away travel details",
                "Travel details still need to be confirmed.",
                lane_id="personal",
                created_at="2026-04-23T10:07:00+00:00",
                next_action="Confirm the itinerary.",
            ),
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_focus_call_gateway_json",
        lambda **kwargs: {
            "items": [
                {
                    "id": "travel",
                    "title": "Confirm flights and hotel",
                    "status": "Move to the top",
                    "next_action": "Lock flights and hotel tonight.",
                    "detail_md": "Travel is first until the flights and hotel are confirmed.",
                },
                {
                    "id": "bank",
                    "title": "Finish bank paperwork",
                    "status": "Second",
                    "next_action": "Wrap the paperwork after travel is locked.",
                    "detail_md": "Keep the banking task active, but second.",
                },
            ]
        },
    )
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Travel first. Rewrite it as confirming flights and hotel, then keep the bank paperwork second.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert [entry["id"] for entry in payload["entries"]] == ["travel", "bank"]
    assert payload["entries"][0]["title"] == "Confirm flights and hotel"
    assert payload["entries"][0]["createdAt"] == "2026-04-23T10:07:00+00:00"
    assert payload["entries"][1]["createdAt"] == "2026-04-23T10:05:00+00:00"


def test_focus_priority_eval_can_clear_personal_manual_focus_when_everything_is_resolved(focus_main, monkeypatch):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "travel",
                "Confirm flights and hotel",
                "Travel is first until the flights and hotel are confirmed.",
                lane_id="personal",
                created_at="2026-04-23T10:07:00+00:00",
                next_action="Lock flights and hotel tonight.",
            ),
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Keep the banking task active, but second.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Wrap the paperwork after travel is locked.",
            ),
        ],
    )
    monkeypatch.setattr(focus_main, "_focus_call_gateway_json", lambda **kwargs: {"items": []})
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Everything in personal manual focus is handled now, so clear that manual layer out.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["entries"] == []
    assert focus_main._load_focus_manual_priorities()["personal"] == []

    overview = client.get("/api/focus/overview").get_json()
    personal_lane = next(lane for lane in overview["lanes"] if lane["id"] == "personal")
    assert all(section["id"] != "manual_priorities" for section in personal_lane["sections"])


def test_focus_priority_eval_can_add_new_item_via_model_revision(focus_main, monkeypatch):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Bank paperwork is still open.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Finish the pending forms.",
            ),
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_focus_call_gateway_json",
        lambda **kwargs: {
            "items": [
                {
                    "id": "bank",
                    "title": "Finish bank paperwork",
                    "status": "Still open",
                    "next_action": "Finish the forms.",
                    "detail_md": "Keep the banking task active.",
                },
                {
                    "id": "",
                    "title": "Square away travel details",
                    "status": "New",
                    "next_action": "Get the travel details squared away before Sunday.",
                    "detail_md": "Travel details still need to be confirmed.",
                },
            ]
        },
    )
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Keep the bank paperwork and add travel details before Sunday.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert [entry["title"] for entry in payload["entries"]] == [
        "Finish bank paperwork",
        "Square away travel details",
    ]
    stored = focus_main._load_focus_manual_priorities()["personal"]
    assert stored[0]["id"] == "bank"
    assert stored[1]["id"]
    assert stored[1]["id"] != "bank"
    assert stored[1]["createdAt"]


def test_focus_priority_eval_falls_back_to_append_when_model_output_is_malformed(focus_main, monkeypatch):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Bank paperwork is still open.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Finish the pending forms.",
            ),
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_focus_call_gateway_json",
        lambda **kwargs: {
            "items": [
                {},
                {"id": "", "title": "", "status": "", "next_action": "", "detail_md": ""},
            ]
        },
    )
    client = focus_main.app.test_client()

    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Add travel details before Sunday and keep the bank paperwork active.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["entries"]) == 2
    assert payload["entries"][0]["detail_md"] == "Add travel details before Sunday and keep the bank paperwork active."
    assert payload["entries"][1]["id"] == "bank"


def test_focus_priority_performance_slow_gateway_falls_back_without_locking_the_route(focus_main, monkeypatch):
    monkeypatch.setattr(focus_main, "_FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S", 0.12)

    def slow_gateway(**kwargs):
        time.sleep(1.0)
        return {"items": []}

    monkeypatch.setattr(focus_main, "_focus_call_gateway_json", slow_gateway)
    client = focus_main.app.test_client()

    started = time.perf_counter()
    response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "personal",
            "text": "Need to confirm Jonas pickup time before Sunday.",
        },
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert elapsed < 0.45
    payload = response.get_json()
    assert payload["entries"][0]["detail_md"] == "Need to confirm Jonas pickup time before Sunday."


def test_focus_priority_eval_query_overview_surfaces_personal_manual_focus_first(focus_main):
    _seed_manual_priorities(
        focus_main,
        personal=[
            _manual_entry(
                "travel",
                "Confirm flights and hotel",
                "Travel is first until the flights and hotel are confirmed.",
                lane_id="personal",
                created_at="2026-04-23T10:07:00+00:00",
                next_action="Lock flights and hotel tonight.",
            ),
            _manual_entry(
                "bank",
                "Finish bank paperwork",
                "Keep the banking task active, but second.",
                lane_id="personal",
                created_at="2026-04-23T10:05:00+00:00",
                next_action="Wrap the paperwork after travel is locked.",
            ),
        ],
    )
    client = focus_main.app.test_client()

    response = client.get("/api/focus/overview")

    assert response.status_code == 200
    payload = response.get_json()
    personal_lane = next(lane for lane in payload["lanes"] if lane["id"] == "personal")
    assert personal_lane["sections"][0]["id"] == "manual_priorities"
    assert personal_lane["sections"][0]["title"] == "Manual Focus"
    assert [item["title"] for item in personal_lane["sections"][0]["items"]] == [
        "Confirm flights and hotel",
        "Finish bank paperwork",
    ]


def test_focus_priority_eval_business_lane_can_add_and_query_manual_focus(focus_main, monkeypatch):
    monkeypatch.setattr(focus_main, "_focus_call_gateway_json", lambda **kwargs: None)
    client = focus_main.app.test_client()

    post_response = client.post(
        "/api/focus/manual-priorities",
        json={
            "laneId": "work",
            "text": "Put the launch review first, remove stale follow-ups, and keep the riskiest business thread visible today.",
        },
    )

    assert post_response.status_code == 200
    overview_response = client.get("/api/focus/overview")
    assert overview_response.status_code == 200

    overview = overview_response.get_json()
    work_lane = next(lane for lane in overview["lanes"] if lane["id"] == "work")
    assert work_lane["sections"][0]["id"] == "manual_priorities"
    assert "launch review" in work_lane["sections"][0]["items"][0]["detail_md"].lower()


def test_focus_priority_performance_tests_run_route_returns_before_worker_finishes(focus_main, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def fake_run_test_job(requested_profile, specs, run_id):
        started.set()
        assert requested_profile == "focus-priorities"
        release.wait(timeout=2.0)
        focus_main._update_test_task(
            running=False,
            finished_at="2026-04-23T19:41:00+00:00",
            returncode=0,
            progress_percent=100,
            progress_line="Completed",
            tail=["[focus-priorities] 1 passed in 0.12s"],
        )
        finished.set()

    monkeypatch.setattr(focus_main, "_run_test_job", fake_run_test_job)
    client = focus_main.app.test_client()

    started_at = time.perf_counter()
    response = client.post("/api/tests/run", json={"profile": "focus-priorities"})
    elapsed = time.perf_counter() - started_at

    assert response.status_code == 200
    assert elapsed < 0.35
    assert started.wait(timeout=1.0)

    status = client.get("/api/tests/status").get_json()["tasks"]["tests"]
    assert status["running"] is True
    assert status["trigger"] == "manual"

    release.set()
    assert finished.wait(timeout=1.0)


def test_focus_priority_automations_status_auto_schedules_missing_profile(focus_main, monkeypatch):
    class ImmediateThread:
        def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}

        def start(self):
            if self._target:
                self._target(*self._args, **self._kwargs)

    monkeypatch.setattr(focus_main.threading, "Thread", ImmediateThread)

    def fake_run_test_job(requested_profile, specs, run_id):
        report = focus_main._build_test_report_from_results(
            profile_id=requested_profile,
            run_id=run_id,
            timestamp_iso="2026-04-23T19:42:00+00:00",
            results=[
                {
                    "name": "tests/test_focus_priority_console_eval.py::test_auto_schedule",
                    "status": "passed",
                    "duration_s": 0.19,
                    "timestamp": "2026-04-23T19:42:00+00:00",
                }
            ],
            failure_analysis={},
        )
        focus_main._save_test_report(requested_profile, run_id, report)
        focus_main._update_test_task(
            running=False,
            finished_at="2026-04-23T19:42:01+00:00",
            returncode=0,
            progress_percent=100,
            progress_line="Completed",
            tail=["[focus-priorities] 1 passed in 0.19s"],
        )

    monkeypatch.setattr(focus_main, "_run_test_job", fake_run_test_job)
    focus_main._update_test_automation_state(
        last_auto_requested_at=None,
        last_auto_profile="",
        last_auto_reason="",
        last_auto_run_id="",
    )
    client = focus_main.app.test_client()

    response = client.get("/api/automations/status")
    assert response.status_code == 200

    payload = response.get_json()
    verification = payload["verification"]["focus-priorities"]
    assert verification["auto_run"]["scheduled"] is True
    assert verification["auto_run"]["reason"] == "missing"

    latest = client.get("/api/test-reports/latest").get_json()["reports"]
    assert latest["focus-priorities"]["report"]["summary"]["passed"] == 1


def test_focus_priority_agent_fleet_surfaces_verifier_and_health_findings(focus_main, monkeypatch):
    monkeypatch.setattr(
        focus_main,
        "load_team_agents",
        lambda: [
            {
                "agent_id": "archivist-verifier",
                "name": "Archivist Verifier",
                "summary": "Validation gate for Archivist builds, tests, and runtime checks.",
            },
            {
                "agent_id": "archivist-health",
                "name": "Archivist Health",
                "summary": "Runtime health monitor for gateway, backups, indexing, and media services.",
            },
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_agent_runtime_snapshot",
        lambda: {"available": True, "registered_agents": ["archivist-verifier", "archivist-health"]},
    )
    report = focus_main._build_test_report_from_results(
        profile_id="focus-priorities",
        run_id="fleet-report",
        timestamp_iso="2026-04-23T19:43:00+00:00",
        results=[
            {
                "name": "tests/test_focus_priority_console_eval.py::test_focus_priority_eval_adds_personal_note_when_gateway_is_unavailable",
                "status": "failed",
                "duration_s": 0.21,
                "timestamp": "2026-04-23T19:43:00+00:00",
            },
            {
                "name": "tests/test_focus_priority_console_eval.py::test_focus_priority_performance_tests_run_route_returns_before_worker_finishes",
                "status": "failed",
                "duration_s": 0.33,
                "timestamp": "2026-04-23T19:43:00+00:00",
            },
        ],
        failure_analysis={
            "manual priority regression": [
                "tests/test_focus_priority_console_eval.py::test_focus_priority_eval_adds_personal_note_when_gateway_is_unavailable",
                "tests/test_focus_priority_console_eval.py::test_focus_priority_performance_tests_run_route_returns_before_worker_finishes",
            ]
        },
    )
    focus_main._save_test_report("focus-priorities", "fleet-report", report)
    client = focus_main.app.test_client()

    response = client.get("/api/agents/fleet")
    assert response.status_code == 200
    payload = response.get_json()

    verifier = next(agent for agent in payload["agents"] if agent["id"] == "archivist-verifier")
    health = next(agent for agent in payload["agents"] if agent["id"] == "archivist-health")
    assert any(finding["ticket_id"] == "focus-priorities-failing" for finding in verifier["findings"])
    assert any(finding["ticket_id"] == "focus-priorities-performance" for finding in health["findings"])


def test_focus_priority_agent_fleet_respects_manifest_visibility_sort_and_lanes(focus_main, monkeypatch):
    monkeypatch.setattr(
        focus_main,
        "load_team_agents",
        lambda: [
            {
                "agent_id": "archivist-repair",
                "name": "Archivist Repair",
                "summary": "Repair worker",
                "role": "repair-worker",
                "_path": "/tmp/repair",
                "ui": {"show": True, "sort_key": 30, "badge": "repair"},
            },
            {
                "agent_id": "hidden-agent",
                "name": "Hidden Agent",
                "summary": "Should not surface",
                "role": "hidden",
                "_path": "/tmp/hidden",
                "ui": {"show": False, "sort_key": 5, "badge": "hidden"},
            },
            {
                "agent_id": "priority-specialist",
                "name": "Priority Specialist",
                "summary": "Specialist lane role",
                "role": "specialist",
                "fleet_lane": "specialist",
                "_path": "/tmp/specialist",
                "ui": {"show": True, "sort_key": 20, "badge": "specialist"},
            },
            {
                "agent_id": "archivist-main",
                "name": "Archivist Main",
                "summary": "Operator",
                "role": "operator",
                "_path": "/tmp/main",
                "ui": {"show": True, "sort_key": 10, "badge": "operator"},
            },
        ],
    )
    monkeypatch.setattr(
        focus_main,
        "_agent_runtime_snapshot",
        lambda: {
            "available": True,
            "registered_agents": ["archivist-main", "archivist-repair", "priority-specialist"],
        },
    )
    monkeypatch.setattr(
        focus_main,
        "_build_focus_priority_verification_snapshot",
        lambda auto_schedule=False: {"tickets": [], "owner_agents": [], "latest": {}, "status": "ok"},
    )
    client = focus_main.app.test_client()

    response = client.get("/api/agents/fleet")
    assert response.status_code == 200

    payload = response.get_json()
    assert [lane["id"] for lane in payload["lanes"]] == ["system", "specialist"]

    system_lane = next(lane for lane in payload["lanes"] if lane["id"] == "system")
    specialist_lane = next(lane for lane in payload["lanes"] if lane["id"] == "specialist")

    assert [agent["id"] for agent in system_lane["agents"]] == ["archivist-main", "archivist-repair"]
    assert [agent["id"] for agent in specialist_lane["agents"]] == ["priority-specialist"]
    assert all(agent["id"] != "hidden-agent" for agent in payload["agents"])
    assert system_lane["agents"][0]["group_label"] == "operator"
    assert system_lane["agents"][0]["registered"] is True
    assert specialist_lane["agents"][0]["lane"] == "specialist"


def test_agent_chat_sessions_capture_console_surface_and_scope(focus_main, monkeypatch):
    class FakeGatewayResponse:
        status_code = 200

        def iter_lines(self, decode_unicode=True):
            yield 'data: {"choices":[{"delta":{"content":"Ready to help."}}]}'
            yield "data: [DONE]"

    monkeypatch.setattr(focus_main, "resolve_gateway_token", lambda: "test-token")
    monkeypatch.setattr(focus_main, "resolve_gateway_url", lambda: "http://gateway.test")
    monkeypatch.setattr(
        focus_main,
        "build_agent_system_message",
        lambda agent_id, screen_context: f"system::{agent_id}::{screen_context}",
    )
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeGatewayResponse())
    client = focus_main.app.test_client()

    response = client.post(
        "/api/agent/chat",
        json={
            "message": "Inspect the console session contract.",
            "surface": "console",
            "historyScope": "main-chat",
            "context": {"page": "Console", "description": "Session metadata test"},
        },
        buffered=True,
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "event: session_start" in body
    assert "Ready to help." in body

    sessions = client.get("/api/agent/sessions").get_json()
    session = next(row for row in sessions if row["surface"] == "console")
    assert session["historyScope"] == "main-chat"
    assert session["agentId"] == "archivist-main"
    assert session["messageCount"] == 2

    detail = client.get(f"/api/agent/sessions/{quote(session['id'], safe='')}")
    assert detail.status_code == 200
    payload = detail.get_json()
    assert payload["agentId"] == "archivist-main"
    assert payload["sessionKey"] == "main:web:test@archivist-main"
    assert payload["surface"] == "console"
    assert payload["historyScope"] == "main-chat"
    assert [message["role"] for message in payload["messages"]] == ["user", "assistant"]


def test_focus_priority_console_runner_profile_persists_report_and_summary(focus_main, monkeypatch):
    class ImmediateThread:
        def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}

        def start(self):
            if self._target:
                self._target(*self._args, **self._kwargs)

    monkeypatch.setattr(focus_main.threading, "Thread", ImmediateThread)

    def fake_run_test_job(requested_profile, specs, run_id):
        assert requested_profile == "focus-priorities"
        assert [spec["id"] for spec in specs] == ["focus-priorities"]
        report = focus_main._build_test_report_from_results(
            profile_id=requested_profile,
            run_id=run_id,
            timestamp_iso="2026-04-23T19:40:00+00:00",
            results=[
                {
                    "name": "tests/test_focus_priority_console_eval.py::test_add",
                    "status": "passed",
                    "duration_s": 0.21,
                    "timestamp": "2026-04-23T19:40:00+00:00",
                },
                {
                    "name": "tests/test_focus_priority_console_eval.py::test_remove",
                    "status": "passed",
                    "duration_s": 0.18,
                    "timestamp": "2026-04-23T19:40:00+00:00",
                },
            ],
            failure_analysis={},
        )
        focus_main._save_test_report(requested_profile, run_id, report)
        focus_main._update_test_task(
            running=False,
            finished_at="2026-04-23T19:40:01+00:00",
            returncode=0,
            progress_percent=100,
            progress_line="Completed",
            tail=["[focus-priorities] 2 passed in 0.39s"],
        )

    monkeypatch.setattr(focus_main, "_run_test_job", fake_run_test_job)
    client = focus_main.app.test_client()

    profiles = client.get("/api/tests/profiles").get_json()
    assert profiles["profiles"] == [{"id": "focus-priorities", "label": "Focus Priority Evals"}]

    run_response = client.post("/api/tests/run", json={"profile": "focus-priorities"})
    assert run_response.status_code == 200
    assert run_response.get_json()["profile"] == "focus-priorities"

    status = client.get("/api/tests/status").get_json()["tasks"]["tests"]
    assert status["running"] is False
    assert status["returncode"] == 0
    assert status["progress_line"] == "Completed"

    latest = client.get("/api/test-reports/latest").get_json()["reports"]
    assert latest["focus-priorities"]["report"]["summary"]["passed"] == 2
    assert latest["focus-priorities"]["report"]["summary"]["total_tests"] == 2

    history = client.get("/api/test-reports/history?limit=5").get_json()["reports"]
    assert history
    assert history[0]["profile_id"] == "focus-priorities"

    summary = client.post("/api/tests/summarize", json={"profile": "focus-priorities"}).get_json()["summary"]
    assert "2/2 passed" in summary
