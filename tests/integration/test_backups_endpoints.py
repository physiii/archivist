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

    # If already running, just verify we can observe status.
    for _ in range(90):
        o = requests.get(f"{BASE_URL}/api/backups/overview", timeout=15).json()
        st = o.get("status") or {}
        if not st.get("running"):
            after = {f["name"] for f in o.get("backup_files", [])}
            # Either a new backup file exists, or one already existed.
            assert after or before
            recent = o.get("recent_runs", [])
            if recent:
                run_id = recent[0]["run_id"]
                logs = requests.get(f"{BASE_URL}/api/backups/runs/{run_id}/logs?tail=50", timeout=15)
                assert logs.status_code == 200
                payload = logs.json()
                assert "summary" in payload
            return
        time.sleep(1)

    raise AssertionError("Backup did not finish within 90s")


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
