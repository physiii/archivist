from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import backups_service


def test_load_backup_config_keeps_literal_source_paths(monkeypatch, tmp_path):
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

    loaded = backups_service._load_backup_config()
    assert loaded["targets"][0]["source"] == "/mass/scripts"
    persisted = json.loads(config_file.read_text(encoding="utf-8"))
    assert persisted["targets"][0]["source"] == "/mass/scripts"


def test_target_health_requires_mount_for_mass_paths(monkeypatch):
    monkeypatch.setattr(backups_service.os.path, "exists", lambda _path: True)
    monkeypatch.setattr(backups_service.os, "access", lambda _path, _mode: True)
    monkeypatch.setattr(
        backups_service,
        "_get_mount_point",
        lambda path: "/" if path.startswith("/media/mass/") else "/home/andy/nas_mass",
    )

    health = backups_service._target_health("nas", "/media/mass/scripts", "/home/andy/nas_mass")
    assert health["source_mount_required"] is True
    assert health["source_mount_ok"] is False
    assert health["destination_mount_ok"] is True
    assert health["ready"] is False


def test_build_rsync_excludes_skips_deleted_volume_tree():
    excludes = backups_service._build_rsync_excludes({"excludes": [], "exclude_hidden": True})
    assert "--exclude=/milvus_DEL/" in excludes
    assert "--exclude=/milvus_DEL/**" in excludes
    assert "--exclude=.*" in excludes
    assert "--exclude=*/.*" in excludes


def test_build_rsync_command_uses_low_priority_low_metadata_flags(monkeypatch):
    monkeypatch.setattr(backups_service, "RSYNC_NICE_LEVEL", 15)
    monkeypatch.setattr(backups_service, "RSYNC_IONICE_CLASS", "idle")
    monkeypatch.setattr(backups_service, "RSYNC_IONICE_LEVEL", 7)
    monkeypatch.setattr(backups_service, "shutil_which", lambda cmd: cmd in {"ionice", "nice", "rsync"})

    command = backups_service._build_rsync_command(
        {"rsync_bwlimit": "12M"},
        "/media/mass/Documents",
        "/home/andy/nas_mass/Documents",
        ["--exclude=.git"],
    )

    assert command[:6] == ["ionice", "-c3", "nice", "-n", "15", "rsync"]
    assert "-rlt" in command
    assert "-aAH" not in command
    assert "--omit-dir-times" in command
    assert "--modify-window=1" in command
    assert "--bwlimit=12M" in command
    assert command[-3:] == ["--exclude=.git", "/media/mass/Documents/", "/home/andy/nas_mass/Documents"]


def test_run_subprocess_with_logs_aborts_stalled_command(tmp_path):
    main_log = tmp_path / "main.log"
    debug_log = tmp_path / "debug.log"

    rc, last_line = backups_service._run_subprocess_with_logs(
        ["bash", "-lc", "sleep 5"],
        main_log,
        debug_log,
        "sync:/media/mass/Documents",
        idle_timeout_seconds=1,
    )

    assert rc == 124
    assert last_line is not None
    assert "aborting stalled command" in last_line
    assert "aborting stalled command" in main_log.read_text(encoding="utf-8")


def test_resolve_archive_inputs_reports_missing_mounts(monkeypatch, tmp_path):
    archive_root = tmp_path / "data"
    (archive_root / "milvus").mkdir(parents=True)
    (archive_root / "minio").mkdir(parents=True)
    monkeypatch.setattr(
        backups_service,
        "ARCHIVE_SOURCE_DIRS",
        [
            (archive_root / "milvus", "milvus"),
            (archive_root / "etcd", "etcd"),
            (archive_root / "minio", "minio"),
        ],
    )

    resolved_root, members, missing = backups_service._resolve_archive_inputs()
    assert resolved_root == archive_root
    assert members == ["milvus", "minio"]
    assert missing == [str(archive_root / "etcd")]


def test_zfs_command_uses_ssh_when_remote_host_configured(monkeypatch):
    monkeypatch.setattr(backups_service, "ZFS_REMOTE_HOST", "192.168.1.42")
    monkeypatch.setattr(backups_service, "ZFS_REMOTE_HOST_LABEL", "megamind")
    monkeypatch.setattr(backups_service, "ZFS_REMOTE_USER", "andy")
    monkeypatch.setattr(backups_service, "ZFS_USE_SUDO", True)
    command = backups_service._zfs_command("zfs", "list", "-Hp", "mass")
    assert command == [
        "ssh",
        "-F",
        "/dev/null",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        "andy@192.168.1.42",
        "sudo",
        "-n",
        "zfs",
        "list",
        "-Hp",
        "mass",
    ]
    assert backups_service._zfs_target_label("mass") == "megamind:mass"


def test_zfs_runtime_available_prefers_ssh_for_remote_host(monkeypatch):
    monkeypatch.setattr(backups_service, "ZFS_REMOTE_HOST", "megamind")
    monkeypatch.setattr(backups_service, "shutil_which", lambda cmd: cmd == "ssh")
    available, error = backups_service._zfs_runtime_available()
    assert available is True
    assert error is None
