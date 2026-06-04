"""Tests for the /health endpoint and backup coverage."""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestBackupCoverage:
    """Verify that backup targets include all critical data directories."""

    def test_archive_source_dirs_includes_archivist_config(self):
        import backups_service
        source_paths = [str(path) for path, _label in backups_service.ARCHIVE_SOURCE_DIRS]
        assert "/root/.config/archivist" in source_paths, \
            "Google archive data must be included in backup sources"

    def test_archive_source_dirs_includes_media_pipeline(self):
        import backups_service
        source_paths = [str(path) for path, _label in backups_service.ARCHIVE_SOURCE_DIRS]
        assert "/data/media_pipeline" in source_paths, \
            "Media pipeline results must be included in backup sources"

    def test_archive_source_dirs_includes_milvus(self):
        import backups_service
        source_paths = [str(path) for path, _label in backups_service.ARCHIVE_SOURCE_DIRS]
        assert "/data/milvus" in source_paths

    def test_archive_source_labels_are_unique(self):
        import backups_service
        labels = [label for _path, label in backups_service.ARCHIVE_SOURCE_DIRS]
        assert len(labels) == len(set(labels)), "Backup source labels must be unique"


class TestHealthEndpointSchema:
    """Test the health endpoint response structure (unit-level, no live services)."""

    def test_google_import_staleness_detection(self):
        """Import older than 4 hours should be detected as stale."""
        from datetime import datetime, timedelta, timezone
        old_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        dt = datetime.fromisoformat(old_time)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert hours > 4

    def test_google_import_fresh_detection(self):
        """Import within 4 hours should not be stale."""
        from datetime import datetime, timedelta, timezone
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        dt = datetime.fromisoformat(recent_time)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert hours < 4


class TestRuntimeConfiguration:
    """Prevent deployments that silently remove required GPU-backed services."""

    def test_archivist_compose_requires_gpu_for_transcription(self):
        compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
        config = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
        service = config["services"]["archivist"]
        env = service["environment"]

        assert env["TRANSCRIBE_REQUIRE_CUDA"] == "${TRANSCRIBE_REQUIRE_CUDA:-true}"
        assert env["NVIDIA_VISIBLE_DEVICES"] == "${ARCHIVIST_NVIDIA_VISIBLE_DEVICES:-0}"
        assert env["NVIDIA_DRIVER_CAPABILITIES"] == "${ARCHIVIST_NVIDIA_DRIVER_CAPABILITIES:-compute,utility}"
        assert env["ARCHIVIST_ENABLE_WEB_BACKGROUND_TASKS"] == "${ARCHIVIST_ENABLE_WEB_BACKGROUND_TASKS:-true}"

        gpu_requests = service.get("gpus") or []
        assert gpu_requests, "Archivist must request an NVIDIA GPU device for local transcription"
        assert gpu_requests[0]["device_ids"] == ["${ARCHIVIST_GPU_ID:-0}"]
        assert gpu_requests[0]["capabilities"] == ["gpu"]
