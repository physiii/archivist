"""Tests for journal freshness, staleness detection, and enrichment."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ARCHIVIST_ENABLE_WEB_BACKGROUND_TASKS", "0")

# main.py requires pymilvus and other heavy deps; skip if unavailable.
try:
    import main as _main_module
    _HAS_MAIN = True
except ImportError:
    _HAS_MAIN = False

needs_main = pytest.mark.skipif(not _HAS_MAIN, reason="main.py deps not available")


@pytest.fixture(autouse=True)
def _reset_journal_cache():
    if not _HAS_MAIN:
        return
    import main

    main._journal_overview_cache = None
    main._journal_overview_cache_time = 0.0
    main._journal_overview_building = False
    main._journal_overview_cache_fingerprint = None
    main._journal_overview_cache_root = None
    yield
    main._journal_overview_cache = None
    main._journal_overview_cache_time = 0.0
    main._journal_overview_building = False
    main._journal_overview_cache_fingerprint = None
    main._journal_overview_cache_root = None


@needs_main
class TestJournalStaleness:
    """Test that the journal API detects and reports stale data."""

    def test_stale_when_import_old(self, tmp_path, monkeypatch):
        """Journal should report stale=True when import is more than 4 hours old."""
        import main

        old_time = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
        archive_dir = tmp_path / "google-archive"
        archive_dir.mkdir()
        (archive_dir / "summary.json").write_text(
            json.dumps({
                "available": True,
                "accountCount": 1,
                "gmailMessages": 10,
                "calendarEvents": 5,
                "dayCount": 1,
                "lastImportedAt": old_time,
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        summary = main._google_archive_summary()
        assert summary["lastImportedAt"] == old_time

    def test_fresh_when_import_recent(self):
        """Import within 4 hours should not be stale."""
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        dt = datetime.fromisoformat(recent_time)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert hours < 4

    def test_stale_when_no_import(self):
        """No lastImportedAt should be stale."""
        last_imported = ""
        assert not last_imported.strip()


@needs_main
class TestJournalDayBucketing:
    """Test that journal correctly buckets records by day."""

    def test_email_records_bucketed_by_day(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        account_dir = archive_dir / "test-account"
        account_dir.mkdir(parents=True)

        emails = [
            {"service": "gmail", "account": "test@test.com", "id": "1", "day": "2026-04-14", "subject": "Test Email 1"},
            {"service": "gmail", "account": "test@test.com", "id": "2", "day": "2026-04-14", "subject": "Test Email 2"},
            {"service": "gmail", "account": "test@test.com", "id": "3", "day": "2026-04-13", "subject": "Yesterday"},
        ]
        (account_dir / "gmail_messages.jsonl").write_text(
            "\n".join(json.dumps(e) for e in emails),
            encoding="utf-8",
        )
        (account_dir / "calendar_events.jsonl").write_text("", encoding="utf-8")
        (account_dir / "drive_files.jsonl").write_text("", encoding="utf-8")
        (account_dir / "chat_messages.jsonl").write_text("", encoding="utf-8")
        (account_dir / "manifest.json").write_text(
            json.dumps({"account": "test@test.com", "imported_at": datetime.now(timezone.utc).isoformat(), "gmailMessages": 3, "calendarEvents": 0, "dayCount": 2}),
            encoding="utf-8",
        )

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        with patch.object(main, "_collect_media_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        days_by_date = {d["date"]: d for d in overview["days"]}
        assert "2026-04-14" in days_by_date
        assert "2026-04-13" in days_by_date
        assert "email" in days_by_date["2026-04-14"]["sources"]

    def test_git_commits_appear_in_journal(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        archive_dir.mkdir(parents=True)

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        git_data = {"2026-04-14": [{"repo": "archivist", "hash": "abc12345", "subject": "fix stuff", "author": "Andy"}]}

        with patch.object(main, "_collect_git_activity_for_days", return_value=git_data), \
             patch.object(main, "_collect_media_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        days_by_date = {d["date"]: d for d in overview["days"]}
        assert "2026-04-14" in days_by_date
        day = days_by_date["2026-04-14"]
        assert "git" in day["sources"]
        assert any(s["key"] == "git" for s in day["signals"])

    def test_drive_and_chat_records_appear_in_journal(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        account_dir = archive_dir / "test-account"
        account_dir.mkdir(parents=True)

        (account_dir / "gmail_messages.jsonl").write_text("", encoding="utf-8")
        (account_dir / "calendar_events.jsonl").write_text("", encoding="utf-8")
        (account_dir / "drive_files.jsonl").write_text(
            json.dumps({"service": "drive", "account": "test@test.com", "id": "file-1", "day": "2026-04-14", "name": "Quarterly Plan"}) + "\n",
            encoding="utf-8",
        )
        (account_dir / "chat_messages.jsonl").write_text(
            json.dumps({"service": "chat", "account": "test@test.com", "id": "msg-1", "day": "2026-04-14", "text": "Need to land the launch checklist today."}) + "\n",
            encoding="utf-8",
        )
        (account_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "account": "test@test.com",
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "gmailMessages": 0,
                    "calendarEvents": 0,
                    "driveFiles": 1,
                    "chatMessages": 1,
                    "dayCount": 1,
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        with patch.object(main, "_collect_media_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        assert overview["driveFiles"] == 1
        assert overview["chatMessages"] == 1
        day = overview["days"][0]
        assert "drive" in day["sources"]
        assert "chat" in day["sources"]
        assert any(signal["key"] == "drive" for signal in day["signals"])
        assert any(signal["key"] == "chat" for signal in day["signals"])

    def test_day_summaries_are_compact_and_tense_aware(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        past_dir = archive_dir / "past-account"
        future_dir = archive_dir / "future-account"
        past_dir.mkdir(parents=True)
        future_dir.mkdir(parents=True)

        (past_dir / "gmail_messages.jsonl").write_text(
            json.dumps(
                {
                    "service": "gmail",
                    "account": "physiphile@gmail.com",
                    "id": "past-1",
                    "day": "2000-01-02",
                    "subject": "Deep work on archive cleanup and review plans",
                }
            ) + "\n",
            encoding="utf-8",
        )
        (past_dir / "calendar_events.jsonl").write_text("", encoding="utf-8")
        (past_dir / "drive_files.jsonl").write_text("", encoding="utf-8")
        (past_dir / "chat_messages.jsonl").write_text("", encoding="utf-8")
        (past_dir / "manifest.json").write_text(
            json.dumps({"account": "physiphile@gmail.com", "imported_at": datetime.now(timezone.utc).isoformat(), "gmailMessages": 1, "calendarEvents": 0, "driveFiles": 0, "chatMessages": 0, "dayCount": 1}),
            encoding="utf-8",
        )

        (future_dir / "gmail_messages.jsonl").write_text("", encoding="utf-8")
        (future_dir / "calendar_events.jsonl").write_text(
            json.dumps(
                {
                    "service": "calendar",
                    "account": "physiphile@gmail.com",
                    "calendar_id": "primary",
                    "id": "future-1",
                    "day": "2099-01-02",
                    "summary": "Launch planning sync with product and infra",
                }
            ) + "\n" + json.dumps(
                {
                    "service": "calendar",
                    "account": "andy@pyfi.org",
                    "calendar_id": "primary",
                    "id": "future-2",
                    "day": "2099-01-02",
                    "summary": "Launch planning sync with product and infra",
                }
            ) + "\n",
            encoding="utf-8",
        )
        (future_dir / "drive_files.jsonl").write_text("", encoding="utf-8")
        (future_dir / "chat_messages.jsonl").write_text("", encoding="utf-8")
        (future_dir / "manifest.json").write_text(
            json.dumps({"account": "andy@pyfi.org", "imported_at": datetime.now(timezone.utc).isoformat(), "gmailMessages": 0, "calendarEvents": 2, "driveFiles": 0, "chatMessages": 0, "dayCount": 1}),
            encoding="utf-8",
        )

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        with patch.object(main, "_collect_media_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        days_by_date = {d["date"]: d for d in overview["days"]}
        assert len(days_by_date["2000-01-02"]["summary"]) <= 220
        assert days_by_date["2000-01-02"]["summary"].startswith("Main signal:")
        assert "archive cleanup" in days_by_date["2000-01-02"]["summary"].lower()
        assert "1 email" not in days_by_date["2000-01-02"]["summary"]
        assert len(days_by_date["2099-01-02"]["summary"]) <= 220
        assert days_by_date["2099-01-02"]["summary"].startswith("Scheduled:")
        assert "Launch planning sync" in days_by_date["2099-01-02"]["summary"]
        assert "both accounts scheduled" in days_by_date["2099-01-02"]["summary"].lower()

    def test_routine_calendar_items_do_not_override_stronger_signals(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        account_dir = archive_dir / "test-account"
        account_dir.mkdir(parents=True)

        (account_dir / "gmail_messages.jsonl").write_text(
            json.dumps(
                {
                    "service": "gmail",
                    "account": "andy@pyfi.org",
                    "id": "email-1",
                    "day": "2026-04-14",
                    "subject": "[GitHub] A personal access token (classic) has been added to your account",
                }
            ) + "\n",
            encoding="utf-8",
        )
        (account_dir / "calendar_events.jsonl").write_text(
            json.dumps(
                {
                    "service": "calendar",
                    "account": "andy@pyfi.org",
                    "id": "event-1",
                    "day": "2026-04-14",
                    "summary": "Recycle and Trash Pickup",
                }
            ) + "\n",
            encoding="utf-8",
        )
        (account_dir / "drive_files.jsonl").write_text("", encoding="utf-8")
        (account_dir / "chat_messages.jsonl").write_text("", encoding="utf-8")
        (account_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "account": "andy@pyfi.org",
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "gmailMessages": 1,
                    "calendarEvents": 1,
                    "driveFiles": 0,
                    "chatMessages": 0,
                    "dayCount": 1,
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        with patch.object(
            main,
            "_collect_git_activity_for_days",
            return_value={"2026-04-14": [{"repo": "archivist", "hash": "abc12345", "subject": "feat: add oauth reauth flow", "author": "Andy"}]},
        ), patch.object(main, "_collect_media_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        day = overview["days"][0]
        assert day["title"] == "Engineering push"
        assert "Recycle and Trash Pickup" not in day["summary"]
        assert "oauth reauth flow" in day["summary"].lower()
        assert day["focus"].lower().startswith("engineering work around")
        assert [section["label"] for section in day["sections"]] == ["What happened", "Work and projects", "Life and logistics"]
        section_text = " ".join(section["text"] for section in day["sections"])
        assert "GitHub event(s)" not in section_text
        assert "calendar event(s)" not in section_text
        assert "Connected account activity came from" not in section_text
        assert day["evidence"]

    def test_media_items_use_source_recording_day_instead_of_processing_day(self, tmp_path, monkeypatch):
        import main
        import media.pipeline as media_pipeline

        archive_dir = tmp_path / "google-archive"
        archive_dir.mkdir(parents=True)
        pipeline_dir = tmp_path / "media-pipeline"
        pipeline_dir.mkdir(parents=True)

        result_payload = {
            "media_id": "media-1",
            "asset": {
                "path": "/media/mass/recording/screens/office/obs/2025-05-20_11-02-22.mkv",
                "filename": "2025-05-20_11-02-22.mkv",
                "modality": "video",
                "duration_s": 3913.6,
                "file_hash": "hash-1",
            },
            "archivist_pipeline": {
                "source_path": "/media/mass/recording/screens/office/obs/2025-05-20_11-02-22.mkv",
                "generated_at": 1776249274.4482965,
            },
            "subject_line": "VOA evaluator replacement strategy and VOI integration setbacks discussed in team standup.",
            "artifacts": [
                {
                    "artifact_id": "artifact-1",
                    "media_id": "media-1",
                    "kind": "subject_line",
                    "start_s": 0.0,
                    "end_s": 3913.6,
                    "content": "VOA evaluator replacement strategy and VOI integration setbacks discussed in team standup.",
                    "confidence": 1.0,
                    "metadata": {},
                    "source_refs": [],
                }
            ],
        }
        (pipeline_dir / "media-1.json").write_text(json.dumps(result_payload), encoding="utf-8")

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])
        monkeypatch.setattr(media_pipeline, "PIPELINE_STORE_DIR", pipeline_dir)

        with patch.object(main, "_collect_git_activity_for_days", return_value={}), \
             patch("github_service.collect_github_activity_for_days", return_value={}):
            overview = main._build_google_journal_overview()

        days_by_date = {d["date"]: d for d in overview["days"]}
        assert "2025-05-20" in days_by_date
        assert "2026-04-14" not in days_by_date
        assert "VOA evaluator replacement strategy" in days_by_date["2025-05-20"]["summary"]

    def test_media_collector_uses_richer_document_context(self, tmp_path, monkeypatch):
        import main
        import media.evidence_store as evidence_store
        import media.pipeline as media_pipeline

        pipeline_dir = tmp_path / "media-pipeline"
        pipeline_dir.mkdir(parents=True)

        result_payload = {
            "media_id": "media-2",
            "asset": {
                "path": "/media/mass/recording/screens/office/obs/recording_2026-04-15_12-11-50.mkv",
                "filename": "recording_2026-04-15_12-11-50.mkv",
                "modality": "video",
                "duration_s": 312.0,
                "file_hash": "hash-2",
            },
            "archivist_pipeline": {
                "source_path": "/media/mass/recording/screens/office/obs/recording_2026-04-15_12-11-50.mkv",
                "generated_at": 1776249274.4482965,
            },
            "subject_line": "AI output constraints, personalization risks, and misalignment concerns in recommendation systems.",
            "document": {
                "full_text": (
                    "## Context Overview\n"
                    "A short conversation explores whether AI recommendation systems should steer what people watch, "
                    "write, or decide, and keeps returning to manipulation and hidden agendas.\n\n"
                    "## Key Topics\n"
                    "- **AI output constraints on user decisions** — whether assistants should avoid pushing people toward specific movies or reviews.\n"
                    "- **Personalization and manipulation risk** — how data collection can become a pathway for pressure or hidden incentives.\n"
                )
            },
            "artifacts": [
                {
                    "artifact_id": "subject-1",
                    "media_id": "media-2",
                    "kind": "subject_line",
                    "content": "AI output constraints, personalization risks, and misalignment concerns in recommendation systems.",
                    "metadata": {},
                },
                {
                    "artifact_id": "memory-1",
                    "media_id": "media-2",
                    "kind": "memory",
                    "content": json.dumps(
                        {
                            "context_overview": "A short conversation explores whether AI recommendation systems should steer what people watch, write, or decide, and keeps returning to manipulation and hidden agendas."
                        }
                    ),
                    "metadata": {},
                },
                {
                    "artifact_id": "document-1",
                    "media_id": "media-2",
                    "kind": "document",
                    "content": (
                        "## Context Overview\n"
                        "A short conversation explores whether AI recommendation systems should steer what people watch, "
                        "write, or decide, and keeps returning to manipulation and hidden agendas.\n\n"
                        "## Key Topics\n"
                        "- **AI output constraints on user decisions** — whether assistants should avoid pushing people toward specific movies or reviews.\n"
                        "- **Personalization and manipulation risk** — how data collection can become a pathway for pressure or hidden incentives.\n"
                    ),
                    "metadata": {},
                },
            ],
        }
        (pipeline_dir / "media-2.json").write_text(json.dumps(result_payload), encoding="utf-8")

        monkeypatch.setattr(media_pipeline, "PIPELINE_STORE_DIR", pipeline_dir)
        monkeypatch.setattr(evidence_store, "PIPELINE_RESULTS_DIR", pipeline_dir)

        activity = main._collect_media_activity_for_days()
        item = activity["2026-04-15"][0]
        assert item["subject"].startswith("AI output constraints")
        assert "movie" in item["theme_text"].lower()
        assert "hidden agendas" in item["theme_text"].lower()
        assert item["weight_multiplier"] > 1.4
        assert item["low_signal"] is False

    def test_rich_media_context_outweighs_github_mechanics(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        archive_dir.mkdir(parents=True)

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)
        monkeypatch.setattr(main, "_ARCHIVIST_GIT_REPO_DIRS", [])

        media_activity = {
            "2026-04-15": [
                {
                    "media_id": "media-ideas",
                    "subject": "AI output constraints, personalization risks, and misalignment concerns in recommendation systems.",
                    "context": "A conversation about whether recommendation systems should influence movie choices, reviews, and user trust.",
                    "theme_text": "AI output constraints personalization risks misalignment recommendation systems movie choices reviews user trust",
                    "weight_multiplier": 1.9,
                    "low_signal": False,
                }
            ]
        }
        github_activity = {
            "2026-04-15": [
                {"type": "create", "title": "Created branch: feat/e2e-dashboard"},
                {"type": "create", "title": "Created branch: feat/connect-lambda-bridge"},
                {"type": "push", "title": "Push"},
                {"type": "push", "title": "Push"},
                {"type": "push", "title": "Push"},
                {"type": "delete", "title": "Deleted branch: feat/e2e-dashboard"},
                {"type": "pr", "title": "Merge pull request #42"},
            ]
        }

        with patch.object(main, "_collect_git_activity_for_days", return_value={}), \
             patch.object(main, "_collect_media_activity_for_days", return_value=media_activity), \
             patch("github_service.collect_github_activity_for_days", return_value=github_activity):
            overview = main._build_google_journal_overview()

        day = {entry["date"]: entry for entry in overview["days"]}["2026-04-15"]
        assert day["title"].startswith("Research")
        assert "Engineering push" not in day["title"]
        assert "recommendation-system trust" in day["summary"]
        assert "Created branch" not in day["summary"]


@needs_main
class TestIncrementalImportDedup:
    """Test that incremental import merges without duplicates."""

    def test_merge_deduplicates_by_id(self, tmp_path, monkeypatch):
        import main

        archive_dir = tmp_path / "google-archive"
        account_dir = archive_dir / main._google_account_slug("test@test.com")
        account_dir.mkdir(parents=True)

        # Existing records
        existing = [
            {"id": "msg1", "subject": "Old Subject 1", "day": "2026-04-10"},
            {"id": "msg2", "subject": "Old Subject 2", "day": "2026-04-11"},
        ]
        (account_dir / "gmail_messages.jsonl").write_text(
            "\n".join(json.dumps(e) for e in existing),
            encoding="utf-8",
        )
        (account_dir / "calendar_events.jsonl").write_text("", encoding="utf-8")

        monkeypatch.setattr(main, "_GOOGLE_ARCHIVE_ROOT", archive_dir)

        # New records with one overlap
        new_records = [
            {"id": "msg2", "subject": "Updated Subject 2", "day": "2026-04-11"},
            {"id": "msg3", "subject": "New Subject 3", "day": "2026-04-12"},
        ]

        manifest = main._write_google_account_archive(
            "test@test.com", new_records, [], [], [], merge=True,
        )

        # Should have 3 unique messages, not 4
        assert manifest["gmailMessages"] == 3

        # msg2 should have the updated subject
        merged = main._jsonl_read(account_dir / "gmail_messages.jsonl")
        by_id = {r["id"]: r for r in merged}
        assert by_id["msg2"]["subject"] == "Updated Subject 2"
        assert "msg1" in by_id
        assert "msg3" in by_id
