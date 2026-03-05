from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import backups_service


def test_load_backup_config_normalizes_legacy_mass_sources(monkeypatch, tmp_path):
    config_file = tmp_path / "backup-config.json"
    config_file.write_text(
        json.dumps(
            {
                "version": 1,
                "backup_pool": "mass",
                "rsync_bwlimit": "20M",
                "sleep_seconds": 5,
                "exclude_hidden": True,
                "excludes": [],
                "targets": [
                    {
                        "id": "t1",
                        "profile": "nas",
                        "source": "/mass/scripts",
                        "destination": "/home/andy/nas_mass",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(backups_service, "BACKUP_ROOT", tmp_path)
    monkeypatch.setattr(backups_service, "BACKUP_CONFIG_FILE", config_file)

    real_exists = backups_service.os.path.exists
    real_ismount = backups_service.os.path.ismount

    def fake_exists(path):
        value = str(path)
        if value in {"/mass/scripts", "/media/mass/scripts"}:
            return True
        return real_exists(path)

    def fake_ismount(path):
        if str(path) == "/mass":
            return False
        return real_ismount(path)

    monkeypatch.setattr(backups_service.os.path, "exists", fake_exists)
    monkeypatch.setattr(backups_service.os.path, "ismount", fake_ismount)

    loaded = backups_service._load_backup_config()
    assert loaded["targets"][0]["source"] == "/media/mass/scripts"
    persisted = json.loads(config_file.read_text(encoding="utf-8"))
    assert persisted["targets"][0]["source"] == "/media/mass/scripts"


def test_target_health_requires_mount_for_mass_paths(monkeypatch):
    monkeypatch.setattr(backups_service.os.path, "exists", lambda _path: True)
    monkeypatch.setattr(backups_service.os, "access", lambda _path, _mode: True)
    monkeypatch.setattr(
        backups_service,
        "_get_mount_point",
        lambda path: "/" if path.startswith("/mass/") else "/home/andy/nas_mass",
    )

    health = backups_service._target_health("nas", "/mass/scripts", "/home/andy/nas_mass")
    assert health["source_mount_required"] is True
    assert health["source_mount_ok"] is False
    assert health["destination_mount_ok"] is True
    assert health["ready"] is False
