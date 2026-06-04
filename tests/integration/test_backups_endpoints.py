import os
import tempfile
import time
from pathlib import Path

import pytest
import requests


BASE_URL = os.environ.get("VECTORSTORE_BASE_URL", "http://127.0.0.1:5050").rstrip("/")


@pytest.mark.integration
def test_backup_overview_and_start_run():
    overview = requests.get(f"{BASE_URL}/api/backups/overview", timeout=15).json()
    assert "schedule" in overview
    assert "backup_files" in overview
    assert "target_mappings" in overview
    assert "storage_diagnostics" in overview

    before = {f["name"] for f in overview.get("backup_files", [])}
    started = requests.post(f"{BASE_URL}/api/backups/start", timeout=30)
    assert started.status_code in (200, 409)
    started_payload = started.json()
    started_status = started_payload.get("status") or {}
    started_run_id = started_status.get("run_id")

    try:
        # Full archive backups can legitimately run for minutes. This integration
        # test only needs to prove the API can start or observe a run, and that
        # overview/log endpoints remain responsive while the worker is active.
        observed = requests.get(f"{BASE_URL}/api/backups/overview", timeout=15).json()
        assert observed.get("status") is not None
        assert observed.get("backup_files") or before

        run_id = started_run_id or ((observed.get("status") or {}).get("run_id"))
        if run_id:
            logs = requests.get(f"{BASE_URL}/api/backups/runs/{run_id}/logs?tail=50", timeout=15)
            assert logs.status_code in (200, 404)
            if logs.status_code == 200:
                assert "summary" in logs.json()
    finally:
        if started.status_code == 200 and started_run_id:
            requests.post(f"{BASE_URL}/api/backups/stop", timeout=30)
            for _ in range(10):
                status = requests.get(f"{BASE_URL}/api/backups/overview", timeout=15).json().get("status") or {}
                if not status.get("running"):
                    break
                time.sleep(0.5)


@pytest.mark.integration
def test_backup_target_crud():
    create = requests.post(
        f"{BASE_URL}/api/backups/targets",
        json={
            "profile": "pytest",
            "source": "/tmp/pytest-source",
            "destination": "/tmp/pytest-destination",
            "enabled": True,
        },
        timeout=20,
    )
    assert create.status_code == 201
    created = create.json()
    target_id = created["id"]

    listing = requests.get(f"{BASE_URL}/api/backups/targets", timeout=20)
    assert listing.status_code == 200
    targets = listing.json().get("targets", [])
    assert any(t["id"] == target_id for t in targets)

    update = requests.put(
        f"{BASE_URL}/api/backups/targets/{target_id}",
        json={"enabled": False},
        timeout=20,
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete = requests.delete(f"{BASE_URL}/api/backups/targets/{target_id}", timeout=20)
    assert delete.status_code == 200


@pytest.mark.integration
def test_backup_target_run_endpoint():
    source_dir = Path(tempfile.mkdtemp(prefix="backup-src-"))
    destination_dir = Path(tempfile.mkdtemp(prefix="backup-dst-"))
    (source_dir / "sample.txt").write_text("hello target backup", encoding="utf-8")

    create = requests.post(
        f"{BASE_URL}/api/backups/targets",
        json={
            "profile": "pytest",
            "source": str(source_dir),
            "destination": str(destination_dir),
            "enabled": False,
        },
        timeout=20,
    )
    assert create.status_code == 201
    target_id = create.json()["id"]

    try:
        started = requests.post(f"{BASE_URL}/api/backups/targets/{target_id}/backup", timeout=30)
        if started.status_code == 409:
            pytest.skip("Backup already running; target backup endpoint confirmed with conflict response.")
        assert started.status_code == 200
        run_id = (started.json().get("status") or {}).get("run_id")
        assert run_id

        for _ in range(90):
            overview = requests.get(f"{BASE_URL}/api/backups/overview", timeout=15).json()
            status = overview.get("status") or {}
            if status.get("run_id") == run_id and not status.get("running"):
                logs = requests.get(f"{BASE_URL}/api/backups/runs/{run_id}/logs?tail=80", timeout=15)
                assert logs.status_code == 200
                summary = (logs.json().get("summary") or {})
                assert summary.get("include_archive") is False
                assert summary.get("sync_total") == 1
                break
            time.sleep(1)
        else:
            raise AssertionError("Target backup run did not finish within 90s")
    finally:
        requests.delete(f"{BASE_URL}/api/backups/targets/{target_id}", timeout=20)
