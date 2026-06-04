import json
import importlib.util
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, relative_path: str):
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


def _load_main_with_stubs(monkeypatch):
    monkeypatch.setenv("ARCHIVIST_ENABLE_WEB_BACKGROUND_TASKS", "0")
    load_stub = types.ModuleType("load")
    load_stub.load_to_vectorstore = lambda *a, **k: None
    load_stub.load_text_to_vectorstore = lambda *a, **k: {"ok": True}
    load_stub.clear_vectorstore_collection = lambda *a, **k: {"ok": True}
    monkeypatch.setitem(sys.modules, "load", load_stub)

    search_stub = types.ModuleType("search")
    search_stub.CollectionLoadError = RuntimeError
    search_stub.search_vectorstore = lambda *a, **k: []
    monkeypatch.setitem(sys.modules, "search", search_stub)

    backups_stub = types.ModuleType("backups_service")
    backups_stub.BACKUP_ROOT = "/tmp"
    backups_stub.add_backup_target = lambda *a, **k: None
    backups_stub.delete_backup_target = lambda *a, **k: None
    backups_stub.get_backup_overview = lambda *a, **k: {"status": {"running": False}}
    backups_stub.get_run_logs = lambda *a, **k: []
    backups_stub.list_backup_files = lambda *a, **k: []
    backups_stub.list_backup_targets = lambda *a, **k: []
    backups_stub.start_backup = lambda *a, **k: None
    backups_stub.start_scheduler_best_effort = lambda *a, **k: None
    backups_stub.start_target_backup = lambda *a, **k: None
    backups_stub.stop_backup = lambda *a, **k: None
    backups_stub.update_backup_target = lambda *a, **k: None
    backups_stub.update_schedule = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "backups_service", backups_stub)

    indexing_stub = types.ModuleType("indexing_service")
    indexing_stub.GOOGLE_ARCHIVE_CONTENT_VERSION = "google_archive_v1"
    indexing_stub.add_indexing_target = lambda *a, **k: None
    indexing_stub.delete_indexing_target = lambda *a, **k: None
    indexing_stub.get_indexing_overview = lambda *a, **k: {"status": {"running": False}}
    indexing_stub.get_indexing_run_logs = lambda *a, **k: []
    indexing_stub.index_google_archive_content = lambda *a, **k: {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0, "errors": []}
    indexing_stub.list_indexing_targets = lambda *a, **k: []
    indexing_stub.scan_indexing_target = lambda *a, **k: {}
    indexing_stub.start_indexing = lambda *a, **k: None
    indexing_stub.start_scheduler_best_effort = lambda *a, **k: None
    indexing_stub.start_target_indexing = lambda *a, **k: None
    indexing_stub.stop_indexing = lambda *a, **k: None
    indexing_stub.update_indexing_target = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "indexing_service", indexing_stub)

    movietime_stub = types.ModuleType("movietime_items")
    movietime_stub.search_movietime_items = lambda *a, **k: []
    movietime_stub.upsert_movietime_items = lambda *a, **k: {"ok": True}
    monkeypatch.setitem(sys.modules, "movietime_items", movietime_stub)

    chat_store_stub = types.ModuleType("chat_store")
    chat_store_stub.add_message = lambda *a, **k: None
    chat_store_stub.create_session = lambda *a, **k: {"id": "session-1"}
    chat_store_stub.delete_session = lambda *a, **k: None
    chat_store_stub.get_session_messages = lambda *a, **k: []
    chat_store_stub.init_db = lambda *a, **k: None
    chat_store_stub.list_sessions = lambda *a, **k: []
    chat_store_stub.update_session_title = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "chat_store", chat_store_stub)

    transcription_stub = types.ModuleType("transcription_service")
    transcription_stub.init_transcription_model = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "transcription_service", transcription_stub)

    agent_stub = types.ModuleType("agent_integration")
    agent_stub.build_agent_system_message = lambda *a, **k: "system"
    agent_stub.console_agent_id = lambda: "operator-chat"
    agent_stub.decode_session_ref = lambda raw=None: ("operator-chat", raw or "main:web:test@operator-chat")
    agent_stub.default_web_session_key = lambda agent_id=None: "main:web:test@operator-chat"
    agent_stub.encode_session_ref = lambda agent_id, session_key: f"agent:{agent_id}:{session_key}"
    agent_stub.agent_session_key = lambda *a, **k: "executor:web:test@operator-chat"
    agent_stub.agents_repo_root = lambda: REPO_ROOT
    agent_stub.host_workspace = lambda: str(REPO_ROOT)
    agent_stub.inspect_agent_runtime = lambda: {"available": False}
    agent_stub.load_agent_messages_from_transcript = lambda *a, **k: []
    agent_stub.load_agent_sessions_for_agents = lambda *a, **k: []
    agent_stub.load_mcp_resources_for_status = lambda *a, **k: []
    agent_stub.load_mcp_tools_for_status = lambda *a, **k: []
    agent_stub.load_shared_skills = lambda *a, **k: []
    agent_stub.load_team_agents = lambda: []
    agent_stub.registered_agent_ids = lambda *a, **k: []
    agent_stub.resolve_agent_chat_model = lambda *a, **k: "agents/operator-chat"
    agent_stub.resolve_agent_executor_token = lambda: ""
    agent_stub.resolve_agent_executor_url = lambda: "/media/mass/agents"
    agent_stub.resolve_agent_session_file = lambda *a, **k: None
    agent_stub.session_kind = lambda *a, **k: "chat"
    agent_stub.visible_agent_ids = lambda: ["operator-chat"]
    monkeypatch.setitem(sys.modules, "agent_integration", agent_stub)

    return _load_module("archivist_main_google_test", "main.py")


def test_google_token_file_candidates_reads_legacy_and_account_dirs(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    legacy = tmp_path / "google_token.json"
    account_dir = tmp_path / "google-accounts"
    account_dir.mkdir()
    work = account_dir / "work@example.com.json"
    personal = account_dir / "personal@example.com.json"
    legacy.write_text("{}", encoding="utf-8")
    work.write_text("{}", encoding="utf-8")
    personal.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main, "_GOOGLE_TOKEN_PATHS", [str(legacy)])
    monkeypatch.setattr(main, "_GOOGLE_ACCOUNT_TOKEN_DIRS", [str(account_dir)])

    paths = main._google_token_file_candidates()
    assert paths == [legacy, personal, work]


def test_google_account_token_path_uses_slugged_email(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    monkeypatch.setattr(main, "_GOOGLE_ACCOUNT_TOKEN_DIRS", [str(tmp_path / "google-accounts")])

    token_path = main._google_account_token_path("Andy.Work+Archive@Example.com")

    assert token_path == tmp_path / "google-accounts" / "andy.work-archive-example.com.json"


def test_google_requested_scopes_include_enabled_chat_and_extra_scopes(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    monkeypatch.setenv("ARCHIVIST_GOOGLE_SERVICES", "gmail, calendar, drive, chat")
    monkeypatch.setenv(
        "ARCHIVIST_GOOGLE_EXTRA_SCOPES",
        "https://www.googleapis.com/auth/chat.messages.readonly https://www.googleapis.com/auth/chat.memberships.readonly",
    )

    assert main._google_requested_scopes() == [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/chat.spaces.readonly",
        "https://www.googleapis.com/auth/chat.messages.readonly",
        "https://www.googleapis.com/auth/chat.memberships.readonly",
    ]


def test_collect_google_accounts_prefers_named_account_token_over_legacy(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    legacy = tmp_path / "google_token.json"
    account_dir = tmp_path / "google-accounts"
    account_dir.mkdir()
    modern = account_dir / "andy@example.com.json"
    legacy.write_text("{}", encoding="utf-8")
    modern.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main, "_GOOGLE_TOKEN_PATHS", [str(legacy)])
    monkeypatch.setattr(main, "_GOOGLE_ACCOUNT_TOKEN_DIRS", [str(account_dir)])

    def _fake_load_google_creds(token_path):
        return {"token_path": str(token_path)}, None, str(token_path)

    def _fake_check_gmail(creds):
        return {
            "id": "gmail",
            "name": "Gmail",
            "description": "Email archive & search",
            "connected": True,
            "status": "connected",
            "account": "andy@example.com",
        }

    def _fake_named_service(service_id, name, description):
        return lambda creds: {
            "id": service_id,
            "name": name,
            "description": description,
            "connected": True,
            "status": "connected",
        }

    monkeypatch.setattr(main, "_load_google_creds", _fake_load_google_creds)
    monkeypatch.setattr(main, "_check_gmail", _fake_check_gmail)
    monkeypatch.setattr(
        main,
        "_check_calendar",
        _fake_named_service("google-calendar", "Google Calendar", "Calendar events & scheduling"),
    )
    monkeypatch.setattr(
        main,
        "_check_drive",
        _fake_named_service("google-drive", "Google Drive", "Document & file archive"),
    )

    accounts = main._collect_google_accounts()

    assert len(accounts) == 1
    assert accounts[0]["account"] == "andy@example.com"
    assert accounts[0]["legacy"] is False
    assert accounts[0]["token_path"] == str(modern)


def test_integrations_status_flattens_multi_account_google_results(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    accounts = [
        {
            "id": "work",
            "label": "work@example.com",
            "account": "work@example.com",
            "connected": True,
            "fully_connected": True,
            "connected_services": 3,
            "service_count": 3,
            "services": [
                {"id": "gmail", "name": "Gmail", "description": "Email archive & search", "connected": True, "status": "connected"},
                {"id": "google-calendar", "name": "Google Calendar", "description": "Calendar events & scheduling", "connected": True, "status": "connected"},
                {"id": "google-drive", "name": "Google Drive", "description": "Document & file archive", "connected": True, "status": "connected"},
            ],
        },
        {
            "id": "personal",
            "label": "personal@example.com",
            "account": "personal@example.com",
            "connected": True,
            "fully_connected": False,
            "connected_services": 2,
            "service_count": 3,
            "services": [
                {"id": "gmail", "name": "Gmail", "description": "Email archive & search", "connected": True, "status": "connected"},
                {"id": "google-calendar", "name": "Google Calendar", "description": "Calendar events & scheduling", "connected": False, "status": "needs_auth"},
                {"id": "google-drive", "name": "Google Drive", "description": "Document & file archive", "connected": True, "status": "connected"},
            ],
        },
    ]

    monkeypatch.setattr(main, "_collect_google_accounts", lambda: accounts)
    monkeypatch.setattr(
        main,
        "_google_summary",
        lambda received_accounts: {
            "connected": True,
            "configured": True,
            "accountCount": len(received_accounts),
            "connectedAccountCount": 2,
            "fullyConnectedAccountCount": 1,
            "accounts": received_accounts,
            "services": [],
            "tokenPaths": [],
            "clientSecretPath": None,
        },
    )

    client = main.app.test_client()
    response = client.get("/api/integrations/status")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["google"]["accountCount"] == 2
    google_integrations = [i for i in payload["integrations"] if i.get("id") != "github"]
    assert len(google_integrations) == 6
    assert {item["account"] for item in google_integrations} == {"work@example.com", "personal@example.com"}


def test_integrations_authorize_returns_auth_url(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    secret = tmp_path / "client_secret.json"
    secret.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "_GOOGLE_CLIENT_SECRET_PATHS", [str(secret)])
    monkeypatch.setenv("ARCHIVIST_GOOGLE_SERVICES", "gmail,calendar,drive")
    main._GOOGLE_AUTH_PENDING.clear()

    google_pkg = types.ModuleType("google_auth_oauthlib")
    google_flow = types.ModuleType("google_auth_oauthlib.flow")

    class FakeFlow:
        def __init__(self):
            self.redirect_uri = None
            self.code_verifier = "test-code-verifier"

        @classmethod
        def from_client_secrets_file(cls, filename, scopes, state=None):
            flow = cls()
            flow.filename = filename
            flow.scopes = scopes
            flow.state = state
            return flow

        def authorization_url(self, **kwargs):
            return ("https://accounts.google.com/o/oauth2/v2/auth?state=test-state", "test-state")

    google_flow.Flow = FakeFlow
    google_pkg.flow = google_flow
    sys.modules["google_auth_oauthlib"] = google_pkg
    sys.modules["google_auth_oauthlib.flow"] = google_flow

    client = main.app.test_client()
    response = client.post("/api/integrations/authorize", json={})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["pending"] is True
    assert payload["auth_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert payload["redirect_uri"].endswith("/api/integrations/oauth/google/callback")
    assert payload["requested_scopes"] == [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    assert [service["id"] for service in payload["services"]] == [
        "gmail",
        "google-calendar",
        "google-drive",
    ]
    assert main._GOOGLE_AUTH_PENDING["test-state"]["code_verifier"] == "test-code-verifier"


def test_integrations_authorize_includes_chat_scopes_when_enabled(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    secret = tmp_path / "client_secret.json"
    secret.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "_GOOGLE_CLIENT_SECRET_PATHS", [str(secret)])
    monkeypatch.setenv("ARCHIVIST_GOOGLE_SERVICES", "gmail,calendar,drive,chat")
    main._GOOGLE_AUTH_PENDING.clear()

    google_pkg = types.ModuleType("google_auth_oauthlib")
    google_flow = types.ModuleType("google_auth_oauthlib.flow")

    class FakeFlow:
        def __init__(self):
            self.redirect_uri = None
            self.code_verifier = "test-code-verifier"

        @classmethod
        def from_client_secrets_file(cls, filename, scopes, state=None):
            flow = cls()
            flow.filename = filename
            flow.scopes = scopes
            flow.state = state
            return flow

        def authorization_url(self, **kwargs):
            return ("https://accounts.google.com/o/oauth2/v2/auth?state=test-state", "test-state")

    google_flow.Flow = FakeFlow
    google_pkg.flow = google_flow
    sys.modules["google_auth_oauthlib"] = google_pkg
    sys.modules["google_auth_oauthlib.flow"] = google_flow

    client = main.app.test_client()
    response = client.post("/api/integrations/authorize", json={})

    assert response.status_code == 200
    payload = response.get_json()
    assert "https://www.googleapis.com/auth/chat.spaces.readonly" in payload["requested_scopes"]
    assert "https://www.googleapis.com/auth/chat.messages.readonly" in payload["requested_scopes"]
    assert [service["id"] for service in payload["services"]] == [
        "gmail",
        "google-calendar",
        "google-drive",
        "google-chat",
    ]


def test_integrations_authorize_callback_restores_code_verifier(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    secret = tmp_path / "client_secret.json"
    secret.write_text("{}", encoding="utf-8")
    main._GOOGLE_AUTH_PENDING.clear()
    main._GOOGLE_AUTH_PENDING["state-1"] = {
        "created_at": 9999999999,
        "label_hint": "andy@example.com",
        "client_secret": str(secret),
        "redirect_uri": "http://127.0.0.1:5050/api/integrations/oauth/google/callback",
        "code_verifier": "saved-verifier",
    }

    captured: dict[str, str | None] = {"code_verifier": None}

    google_pkg = types.ModuleType("google_auth_oauthlib")
    google_flow = types.ModuleType("google_auth_oauthlib.flow")

    class FakeCredentials:
        def to_json(self):
            return '{"token":"abc"}'

    class FakeFlow:
        def __init__(self):
            self.redirect_uri = None
            self.code_verifier = None
            self.credentials = FakeCredentials()

        @classmethod
        def from_client_secrets_file(cls, filename, scopes, state=None):
            flow = cls()
            flow.filename = filename
            flow.scopes = scopes
            flow.state = state
            return flow

        def fetch_token(self, authorization_response=None):
            captured["code_verifier"] = self.code_verifier

    google_flow.Flow = FakeFlow
    google_pkg.flow = google_flow
    sys.modules["google_auth_oauthlib"] = google_pkg
    sys.modules["google_auth_oauthlib.flow"] = google_flow

    monkeypatch.setattr(main, "_discover_google_account_email", lambda creds: "andy@example.com")
    monkeypatch.setattr(main, "_GOOGLE_ACCOUNT_TOKEN_DIRS", [str(tmp_path / "google-accounts")])

    client = main.app.test_client()
    response = client.get(
        "/api/integrations/oauth/google/callback?state=state-1&code=abc",
        base_url="http://127.0.0.1:5050",
    )

    assert response.status_code == 200
    assert captured["code_verifier"] == "saved-verifier"


def test_google_service_since_date_requires_existing_service_file(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    archive_dir = tmp_path / "google-archive"
    account_dir = archive_dir / main._google_account_slug("andy@example.com")
    account_dir.mkdir(parents=True)
    (account_dir / "manifest.json").write_text('{"imported_at":"2026-04-15T12:00:00+00:00"}', encoding="utf-8")

    monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)

    assert main._google_service_since_date("andy@example.com", "drive", incremental=True) is None

    (account_dir / "drive_files.jsonl").write_text("", encoding="utf-8")
    assert main._google_service_since_date("andy@example.com", "drive", incremental=True) == "2026/04/14"


def test_google_service_since_date_calendar_uses_recent_event_window(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    archive_dir = tmp_path / "google-archive"
    account_dir = archive_dir / main._google_account_slug("andy@example.com")
    account_dir.mkdir(parents=True)
    (account_dir / "manifest.json").write_text('{"imported_at":"2026-04-22T12:00:00+00:00"}', encoding="utf-8")
    (account_dir / "calendar_events.jsonl").write_text(
        json.dumps({"service": "calendar", "account": "andy@example.com", "id": "old", "day": "2026-03-21"}) + "\n",
        encoding="utf-8",
    )

    class _FakeDateTime(main.datetime):
        @classmethod
        def now(cls, tz=None):
            base = cls(2026, 4, 23, 12, 0, 0, tzinfo=main.timezone.utc)
            if tz is None:
                return base.replace(tzinfo=None)
            return base.astimezone(tz)

    monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
    monkeypatch.setattr(main, "datetime", _FakeDateTime)
    monkeypatch.setattr(main, "_GOOGLE_CALENDAR_INCREMENTAL_LOOKBACK_DAYS", 45)

    assert main._google_service_since_date("andy@example.com", "calendar", incremental=True) == "2026/03/09"


def test_google_archive_needs_index_sync_tracks_archive_fingerprint(monkeypatch, tmp_path):
    main = _load_main_with_stubs(monkeypatch)
    archive_dir = tmp_path / "google-archive"
    account_dir = archive_dir / "andy-example.com"
    account_dir.mkdir(parents=True)
    (account_dir / "manifest.json").write_text(
        json.dumps(
            {
                "account": "andy@example.com",
                "imported_at": "2026-04-15T12:00:00+00:00",
                "gmailMessages": 3,
                "calendarEvents": 1,
                "driveFiles": 2,
                "chatMessages": 0,
                "dayCount": 2,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)

    needs_sync, reason = main._google_archive_needs_index_sync()
    assert needs_sync is True
    assert reason == "missing-status"

    fingerprint = main._google_archive_fingerprint()
    (archive_dir / "index_status.json").write_text(
        json.dumps(
            {
                "status": "synced",
                "archiveFingerprint": fingerprint,
                "archiveVersion": main.GOOGLE_ARCHIVE_CONTENT_VERSION,
                "embeddingModel": main.LOCAL_EMBEDDING_MODEL,
            }
        ),
        encoding="utf-8",
    )

    needs_sync, reason = main._google_archive_needs_index_sync()
    assert needs_sync is False
    assert reason == "synced"


def test_run_google_import_job_uses_drive_and_indexes_archive(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    monkeypatch.setenv("ARCHIVIST_GOOGLE_SERVICES", "gmail,calendar,drive")

    main._GOOGLE_IMPORT_STATE.update(
        {"running": True, "message": None, "startedAt": None, "finishedAt": None, "accounts": []}
    )
    monkeypatch.setattr(
        main,
        "_collect_google_accounts",
        lambda: [{"account": "andy@example.com", "label": "andy@example.com", "token_path": "/tmp/token.json"}],
    )
    monkeypatch.setattr(main, "_load_google_creds", lambda token_path: ({"token": token_path}, None, token_path))
    monkeypatch.setattr(main, "_fetch_google_gmail_records", lambda *a, **k: [{"service": "gmail", "account": "andy@example.com", "id": "m1", "day": "2026-04-15"}])
    monkeypatch.setattr(main, "_fetch_google_calendar_records", lambda *a, **k: [])
    monkeypatch.setattr(main, "_fetch_google_drive_records", lambda *a, **k: [{"service": "drive", "account": "andy@example.com", "id": "f1", "day": "2026-04-15"}])
    monkeypatch.setattr(main, "_google_service_since_date", lambda *a, **k: None)

    captured = {"write": None, "index_services": None}

    def _fake_write(account_email, gmail_records, calendar_records, drive_records, chat_records, *, merge=False):
        captured["write"] = {
            "account": account_email,
            "gmail": len(gmail_records),
            "calendar": len(calendar_records),
            "drive": len(drive_records),
            "chat": len(chat_records),
            "merge": merge,
        }
        return {
            "gmailMessages": len(gmail_records),
            "calendarEvents": len(calendar_records),
            "driveFiles": len(drive_records),
            "chatMessages": len(chat_records),
            "dayCount": 1,
        }

    monkeypatch.setattr(main, "_write_google_account_archive", _fake_write)
    monkeypatch.setattr(
        main,
        "_persist_google_archive_views",
        lambda: {
            "gmailMessages": 1,
            "calendarEvents": 0,
            "driveFiles": 1,
            "chatMessages": 0,
            "dayCount": 1,
        },
    )
    monkeypatch.setattr(main, "_google_archive_root", lambda: Path("/tmp/google-archive-test"))
    monkeypatch.setattr(main, "check_embedding_service", lambda **kwargs: {"status": "ok"})

    def _fake_index(root, **kwargs):
        captured["index_services"] = kwargs.get("services")
        return {"records_indexed": 2, "chunks_inserted": 2, "errors": []}

    monkeypatch.setattr(main, "index_google_archive_content", _fake_index)

    main._run_google_import_job(services=["gmail", "drive"], incremental=True)

    assert captured["write"] == {
        "account": "andy@example.com",
        "gmail": 1,
        "calendar": 0,
        "drive": 1,
        "chat": 0,
        "merge": True,
    }
    assert captured["index_services"] == {"gmail", "drive"}
    assert "1 drive files" in main._GOOGLE_IMPORT_STATE["message"]


def test_google_archive_index_sync_skips_when_embeddings_down(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    writes = []
    monkeypatch.setattr(
        main,
        "_persist_google_archive_views",
        lambda: {
            "gmailMessages": 1,
            "calendarEvents": 0,
            "driveFiles": 0,
            "chatMessages": 0,
            "dayCount": 1,
        },
    )
    monkeypatch.setattr(main, "_google_archive_fingerprint", lambda *a, **k: "fingerprint")
    monkeypatch.setattr(main, "_write_google_archive_index_status", lambda payload: writes.append(payload))
    monkeypatch.setattr(
        main,
        "check_embedding_service",
        lambda **kwargs: {"status": "error", "error": "embedding backend down"},
    )
    monkeypatch.setattr(
        main,
        "index_google_archive_content",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("indexing should be skipped")),
    )

    summary, index_summary = main._run_google_archive_index_sync(["gmail"])

    assert summary["gmailMessages"] == 1
    assert index_summary["errors"] == ["embedding backend down"]
    assert writes[-1]["status"] == "skipped"
    assert writes[-1]["reason"] == "embeddings_unavailable"


def test_build_work_focus_lane_prefers_latest_week_notes(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    week4 = tmp_path / "WEEK4"
    week5 = tmp_path / "WEEK5"
    week4.mkdir()
    week5.mkdir()

    week4_focus = """# Focus — Week 4
Andy Payne
> Earlier week.

## This Week — Priority Order
| # | What | Owner | Status | Next action |
| --- | --- | --- | --- | --- |
| 1 | Wrap week 4 | Andy | done | Archive it |
"""
    week5_focus = """# Focus — Week 5
Andy Payne
> Current week.

## This Week — Priority Order
| # | What | Owner | Status | Next action |
| --- | --- | --- | --- | --- |
| 1 | Ship dashboard | Andy | active | Finish review |
"""
    (week4 / "FOCUS.md").write_text(week4_focus, encoding="utf-8")
    (week5 / "FOCUS.md").write_text(week5_focus, encoding="utf-8")
    (week5 / "SCHEDULE.md").write_text("# Schedule", encoding="utf-8")
    (tmp_path / "JOURNAL.md").write_text("# Journal", encoding="utf-8")

    monkeypatch.setattr(main, "_FOCUS_WORK_NOTES_ROOT", tmp_path)

    lane = main._build_work_focus_lane()

    assert lane["id"] == "work"
    assert lane["title"] == "Business"
    assert lane["available"] is True
    assert lane["sourcePath"].endswith("WEEK5/FOCUS.md")
    assert lane["sourceLabel"] == "Latest business notes · WEEK5"
    assert lane["sections"][0]["items"][0]["title"] == "Ship dashboard"


def test_build_work_focus_lane_uses_versant_docs_with_default_notes_root(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    default_notes = tmp_path / "vnotes"
    versant_root = tmp_path / "versant-home" / "versant"
    week7 = versant_root / "WEEK7"
    week7.mkdir(parents=True)
    (week7 / "FOCUS.md").write_text(
        """# Focus — Week 7: 2026-04-27 through 2026-05-01
Andy Payne
> Current Versant focus.

## This Week — Priority Order
| # | What | Owner | Status | Next action |
| --- | --- | --- | --- | --- |
| 1 | Confirm Andy's 10 UCP guest pass is live | Andy | active | Confirm access |
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(main, "_DEFAULT_FOCUS_WORK_NOTES_ROOT", default_notes)
    monkeypatch.setattr(main, "_FOCUS_WORK_NOTES_ROOT", default_notes)
    monkeypatch.setattr(main, "_FOCUS_VERSANT_DOCS_ROOT", versant_root)

    lane = main._build_work_focus_lane()

    assert lane["sourceLabel"] == "Versant docs · WEEK7"
    assert lane["sourcePath"].endswith("versant-home/versant/WEEK7/FOCUS.md")
    assert lane["sections"][0]["id"] == "priorities"
    assert lane["sections"][0]["items"][0]["title"] == "Confirm Andy's 10 UCP guest pass is live"


def test_build_work_focus_lane_keeps_priorities_first_with_stale_fallback_notes(tmp_path, monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    archive_dir = tmp_path / "google-archive"
    account_dir = archive_dir / main._google_account_slug("andy@pyfi.org")
    account_dir.mkdir(parents=True)
    (account_dir / "calendar_events.jsonl").write_text(
        json.dumps(
            {
                "service": "calendar",
                "account": "andy@pyfi.org",
                "calendar_summary": "Work",
                "id": "caddy-standup",
                "summary": "Caddy production sampling review",
                "description": "Review live call quality and follow-up work.",
                "start": "2026-04-23T10:00:00-05:00",
                "day": "2026-04-23",
                "attendees": ["garrett@example.com"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    fallback_focus = tmp_path / "FOCUS.md"
    fallback_focus.write_text(
        """# Focus — Week 5: 2026-04-13 through 2026-04-17
Andy Payne
> Old notes.

## This Week — Priority Order
| # | What | Owner | Status | Next Action |
|---|------|-------|--------|-------------|
| 1 | Old priority | Andy | stale | Update it |
""",
        encoding="utf-8",
    )

    class _FakeDateTime(main.datetime):
        @classmethod
        def now(cls, tz=None):
            base = cls(2026, 4, 23, 12, 0, 0, tzinfo=main.timezone.utc)
            if tz is None:
                return base.replace(tzinfo=None)
            return base.astimezone(tz)

    monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
    monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])
    monkeypatch.setattr(main, "_collect_git_activity_for_days", lambda: {})
    monkeypatch.setattr(main, "_collect_media_activity_for_days", lambda: {})
    monkeypatch.setattr(main, "_FOCUS_WORK_NOTES_ROOT", tmp_path / "missing-vnotes")
    monkeypatch.setattr(main, "datetime", _FakeDateTime)
    monkeypatch.setattr(main.Path, "resolve", lambda self: tmp_path / "main.py")
    import github_service
    monkeypatch.setattr(github_service, "collect_github_activity_for_days", lambda: {})

    lane = main._build_work_focus_lane()

    assert lane["sourceLabel"] == "Fallback business notes"
    assert "not found" in lane["sourceWarning"]
    assert lane["sections"][0]["id"] == "priorities"
    assert lane["sections"][0]["items"][0]["title"] == "Old priority"
    assert lane["sections"][1]["id"] == "current_business_signals"
    assert lane["sections"][1]["items"][0]["title"] == "Caddy production sampling review"


def test_focus_business_terms_are_never_personal(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)

    assert main._focus_text_is_work_like("Gigantor execution planning")
    assert main._focus_text_is_work_like("vivonics.ai DNS setup")
    assert main._focus_text_is_work_like("MyVersant performance goals")

    buckets = main._google_archive_story_buckets(
        {
            "notable_mentions": [
                {
                    "source": "email",
                    "text": "VIVONICS.AI DNS renewal payment",
                    "low_signal": False,
                }
            ],
            "supporting_mentions": [],
            "document_topics": [],
        }
    )

    assert buckets["work"]
    assert not buckets["life"]


def test_personal_focus_cleanup_removes_generic_summary_framing(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)

    lane = main._focus_clean_personal_lane(
        {
            "id": "personal",
            "sections": [
                {
                    "id": "priorities",
                    "kind": "priority_table",
                    "items": [
                        {
                            "num": "1",
                            "title": "Planning and coordination around Unconventional Methods",
                            "owner": "Andy",
                            "status": "Upcoming",
                            "next_action": "Scheduled: Unconventional Methods.",
                            "detail_md": "Scheduled: Unconventional Methods.\n\nPrimary signal is Unconventional Methods. Most of the visible signal sits in personal logistics.",
                        }
                    ],
                },
                {
                    "id": "upcoming",
                    "kind": "table",
                    "items": [
                        {
                            "when": "2026-05-08",
                            "event": "Planning and coordination",
                            "why": "Scheduled: Unconventional Methods.",
                        }
                    ],
                },
                {
                    "id": "watchlist",
                    "kind": "list",
                    "items": ["Main signal: Flight to SLC. Related personal/logistics: Flight to OKC."],
                },
            ],
        }
    )

    assert lane["sections"][0]["items"][0]["title"] == "Unconventional Methods"
    assert lane["sections"][0]["items"][0]["next_action"] == "Unconventional Methods"
    assert "Primary signal" not in lane["sections"][0]["items"][0]["detail_md"]
    assert lane["sections"][1]["items"][0]["event"] == "Unconventional Methods"
    assert lane["sections"][2]["items"][0] == "Flight to SLC. Flight to OKC."


def test_focus_overview_response_splits_business_and_personal(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)

    monkeypatch.setattr(
        main,
        "_build_work_focus_lane",
        lambda: {
            "id": "work",
            "title": "Business",
            "available": True,
            "sections": [{"id": "priorities", "title": "Priorities", "kind": "list", "items": ["Ship dashboard"]}],
        },
    )
    monkeypatch.setattr(
        main,
        "_focus_personal_source_context",
        lambda: {"today": "2026-04-15", "fingerprint": "abc123"},
    )
    monkeypatch.setattr(
        main,
        "_focus_personal_lane_for_response",
        lambda _ctx: {
            "id": "personal",
            "title": "Personal",
            "available": True,
            "sections": [{"id": "watchlist", "title": "Watchlist", "kind": "list", "items": ["Handle household admin"]}],
        },
    )
    monkeypatch.setattr(main, "_load_personal_focus_snapshot", lambda: {"generatedAt": "2026-04-15T12:00:00+00:00"})
    monkeypatch.setattr(
        main,
        "_personal_focus_sync_status",
        lambda _ctx, _snapshot: {
            "running": False,
            "message": "Current",
            "stale": False,
            "schedule": {"enabled": True, "time_of_day": "05:30", "timezone": "America/Chicago"},
        },
    )

    payload = main._focus_overview_response()

    assert payload["available"] is True
    assert [lane["id"] for lane in payload["lanes"]] == ["work", "personal"]
    assert payload["lanes"][0]["title"] == "Business"
    assert payload["lanes"][1]["title"] == "Personal"
    assert payload["sync"]["schedule"]["time_of_day"] == "05:30"


def test_personal_focus_snapshot_stays_current_until_morning_sync(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)

    class _FakeDateTime(main.datetime):
        @classmethod
        def now(cls, tz=None):
            base = cls(2026, 4, 16, 9, 0, 0, tzinfo=main.timezone.utc)
            if tz is None:
                return base.replace(tzinfo=None)
            return base.astimezone(tz)

    monkeypatch.setattr(main, 'datetime', _FakeDateTime)
    monkeypatch.setattr(main, '_FOCUS_MAX_AGE_HOURS', 12.0)
    monkeypatch.setattr(main, '_FOCUS_SYNC_TIME_OF_DAY', '05:30')
    monkeypatch.setattr(main, '_FOCUS_SYNC_TIMEZONE', 'America/Chicago')
    monkeypatch.setattr(main, '_google_import_status_public', lambda: {'running': False})

    snapshot = {
        'generatedAt': '2026-04-16T01:30:00+00:00',
        'sourceFingerprint': 'yesterday',
    }
    source_context = {'fingerprint': 'today'}

    assert main._personal_focus_snapshot_stale(snapshot, source_context) is False


def test_personal_focus_snapshot_holds_steady_during_google_import(monkeypatch):
    main = _load_main_with_stubs(monkeypatch)
    monkeypatch.setattr(main, '_google_import_status_public', lambda: {'running': True})

    class _FakeDateTime(main.datetime):
        @classmethod
        def now(cls, tz=None):
            base = cls(2026, 4, 16, 0, 0, 0, tzinfo=main.timezone.utc)
            if tz is None:
                return base.replace(tzinfo=None)
            return base.astimezone(tz)

    monkeypatch.setattr(main, 'datetime', _FakeDateTime)

    snapshot = {
        'generatedAt': '2026-04-15T20:51:21+00:00',
        'sourceFingerprint': 'before-import',
    }
    source_context = {'fingerprint': 'after-import'}

    assert main._personal_focus_snapshot_stale(snapshot, source_context) is False
