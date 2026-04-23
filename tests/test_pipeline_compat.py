"""Tests for pipeline compat version migration and status."""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPipelineCompatStatus:
    """Test compat version detection and reporting."""

    def test_empty_directory(self, tmp_path, monkeypatch):
        from media.pipeline import pipeline_compat_status, PIPELINE_STORE_DIR
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)
        status = pipeline_compat_status()
        assert status["total"] == 0
        assert status["current"] == 0
        assert status["stale"] == 0

    def test_current_results_counted(self, tmp_path, monkeypatch):
        from media.pipeline import pipeline_compat_status, MEDIA_PIPELINE_COMPAT_VERSION
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {
            "archivist_pipeline": {"pipeline_compat_version": MEDIA_PIPELINE_COMPAT_VERSION},
            "document": "some content",
            "transcript": {"text": "hello"},
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        status = pipeline_compat_status()
        assert status["current"] == 1
        assert status["stale"] == 0

    def test_stale_results_counted(self, tmp_path, monkeypatch):
        from media.pipeline import pipeline_compat_status
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {
            "archivist_pipeline": {"pipeline_compat_version": "old-version"},
            "document": "some content",
            "transcript": {"text": "hello"},
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        status = pipeline_compat_status()
        assert status["stale"] == 1
        assert status["current"] == 0

    def test_no_stamp_counted_as_broken(self, tmp_path, monkeypatch):
        from media.pipeline import pipeline_compat_status
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {"document": "some content"}
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        status = pipeline_compat_status()
        assert status["broken"] == 1


class TestPipelineCompatMigration:
    """Test compat version migration."""

    def test_migrate_stamps_stale_results(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version, MEDIA_PIPELINE_COMPAT_VERSION
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        # Create a test file to validate source path checking
        source_file = tmp_path / "test.mkv"
        source_file.write_bytes(b"fake")
        mtime_ns = source_file.stat().st_mtime_ns

        result = {
            "archivist_pipeline": {
                "pipeline_compat_version": "",
                "source_path": str(source_file),
                "source_mtime_ns": mtime_ns,
            },
            "document": "some content",
            "transcript": {"text": "hello"},
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version()
        assert summary["migrated"] == 1
        assert summary["dry_run"] is False

        # Verify the file was updated
        updated = json.loads((tmp_path / "abc123.json").read_text(encoding="utf-8"))
        assert updated["archivist_pipeline"]["pipeline_compat_version"] == MEDIA_PIPELINE_COMPAT_VERSION

    def test_migrate_dry_run_does_not_write(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        source_file = tmp_path / "test.mkv"
        source_file.write_bytes(b"fake")

        result = {
            "archivist_pipeline": {
                "pipeline_compat_version": "",
                "source_path": str(source_file),
                "source_mtime_ns": source_file.stat().st_mtime_ns,
            },
            "document": "content",
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version(dry_run=True)
        assert summary["migrated"] == 1
        assert summary["dry_run"] is True

        # File should NOT be updated
        unchanged = json.loads((tmp_path / "abc123.json").read_text(encoding="utf-8"))
        assert unchanged["archivist_pipeline"]["pipeline_compat_version"] == ""

    def test_migrate_skips_changed_source(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        source_file = tmp_path / "test.mkv"
        source_file.write_bytes(b"fake")

        result = {
            "archivist_pipeline": {
                "pipeline_compat_version": "",
                "source_path": str(source_file),
                "source_mtime_ns": 999999,  # Mismatched mtime
            },
            "document": "content",
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version()
        assert summary["skipped_changed"] == 1
        assert summary["migrated"] == 0

    def test_migrate_skips_missing_source(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {
            "archivist_pipeline": {
                "pipeline_compat_version": "",
                "source_path": "/nonexistent/file.mkv",
                "source_mtime_ns": 12345,
            },
            "document": "content",
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version()
        assert summary["skipped_changed"] == 1

    def test_migrate_skips_already_current(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version, MEDIA_PIPELINE_COMPAT_VERSION
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {
            "archivist_pipeline": {"pipeline_compat_version": MEDIA_PIPELINE_COMPAT_VERSION},
            "document": "content",
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version()
        assert summary["skipped_current"] == 1
        assert summary["migrated"] == 0

    def test_migrate_skips_empty_results(self, tmp_path, monkeypatch):
        from media.pipeline import migrate_pipeline_compat_version
        monkeypatch.setattr("media.pipeline.PIPELINE_STORE_DIR", tmp_path)

        result = {
            "archivist_pipeline": {"pipeline_compat_version": ""},
            # No document or transcript
        }
        (tmp_path / "abc123.json").write_text(json.dumps(result), encoding="utf-8")

        summary = migrate_pipeline_compat_version()
        assert summary["skipped_invalid"] == 1


class TestPipelineResultIsCurrent:
    """Test the freshness check for individual pipeline results."""

    def test_returns_false_for_none_compat_version(self, tmp_path):
        from media.pipeline import _pipeline_result_is_current

        source = tmp_path / "test.mkv"
        source.write_bytes(b"content")

        result = {
            "archivist_pipeline": {
                "pipeline_version": "",
                "pipeline_compat_version": "",
                "source_path": str(source),
                "source_mtime_ns": source.stat().st_mtime_ns,
            },
        }
        assert not _pipeline_result_is_current(result, asset_path=str(source))

    def test_returns_true_for_matching_compat_version(self, tmp_path):
        from media.pipeline import _pipeline_result_is_current, MEDIA_PIPELINE_COMPAT_VERSION

        source = tmp_path / "test.mkv"
        source.write_bytes(b"content")

        result = {
            "archivist_pipeline": {
                "pipeline_compat_version": MEDIA_PIPELINE_COMPAT_VERSION,
                "source_path": str(source.resolve()),
                "source_mtime_ns": source.stat().st_mtime_ns,
            },
        }
        assert _pipeline_result_is_current(result, asset_path=str(source))
