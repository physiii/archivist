from __future__ import annotations

import importlib.util
import json
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    import fcntl  # Linux-only
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore


BACKUP_ROOT = Path(os.getenv("VECTORSTORE_BACKUP_DIR", "/backups"))
RUNS_DIR = BACKUP_ROOT / "runs"
SCHEDULE_STATE_FILE = BACKUP_ROOT / ".backup-schedule.json"
BACKUP_CONFIG_FILE = BACKUP_ROOT / "backup-config.json"
SCHEDULER_LOCK_FILE = BACKUP_ROOT / ".backup-scheduler.lock"
RUN_LOCK_FILE = BACKUP_ROOT / ".backup-run.lock"
RUN_SUMMARY_FILE = "summary.json"

# Canonical docker volume data mounts for the vectorstore stack.
SOURCE_DIRS = [
    (Path("/data/milvus"), "milvus"),
    (Path("/data/etcd"), "etcd"),
    (Path("/data/minio"), "minio"),
]

# Seed values copied from current custodian config.
DEFAULT_EXTERNAL_TARGETS = [
    {"profile": "nas", "source": "/media/mass/scripts", "destination": "/home/andy/nas_mass"},
    {"profile": "nas", "source": "/media/mass/Pictures", "destination": "/home/andy/nas_mass"},
    {"profile": "nas", "source": "/media/mass/Documents", "destination": "/home/andy/nas_mass"},
    {"profile": "nas", "source": "/media/mass/Backup/Glasses", "destination": "/home/andy/nas_mass"},
    {"profile": "nas", "source": "/media/mass/Backup/Phone", "destination": "/home/andy/nas_mass"},
]

DEFAULT_RSYNC_EXCLUDES = [
    "--exclude=.DS_Store",
    "--exclude=Thumbs.db",
    "--exclude=@eaDir/**",
    "--exclude=.Trash-*/**",
]

LEGACY_MASS_PREFIX = "/mass"
CANONICAL_MASS_PREFIX = "/media/mass"


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def _tail(path: Path, lines: int = 120) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as file:
            return "".join(file.readlines()[-lines:])
    except OSError:
        return ""


def _parse_hhmm(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value.strip())
    if not match:
        raise ValueError("time_of_day must be HH:MM (24h).")
    return int(match.group(1)), int(match.group(2))


def _compute_next_run(now: datetime, hhmm: str) -> datetime:
    hour, minute = _parse_hhmm(hhmm)
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        from datetime import timedelta

        candidate = candidate + timedelta(days=1)
    return candidate


def _acquire_lock(path: Path):
    if fcntl is None:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = path.open("w")
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except Exception:
        try:
            fd.close()  # type: ignore
        except Exception:
            pass
        return None


def _new_target_id() -> str:
    return f"target_{uuid4().hex[:12]}"


def _append_log(path: Path, line: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(line.rstrip("\n") + "\n")
    except OSError:
        pass


def _write_run_summary(run_dir: Path, summary: dict[str, Any]) -> None:
    try:
        (run_dir / RUN_SUMMARY_FILE).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except OSError:
        pass


def _read_run_summary(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / RUN_SUMMARY_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _get_mount_point(path: str) -> str:
    current = os.path.abspath(path)
    while current != "/" and not os.path.ismount(current):
        current = os.path.dirname(current)
    return current


def _is_prefixed_path(path: str, prefix: str) -> bool:
    clean = str(path or "").strip()
    return clean == prefix or clean.startswith(f"{prefix}/")


def _requires_separate_mount(path: str) -> bool:
    return _is_prefixed_path(path, LEGACY_MASS_PREFIX) or _is_prefixed_path(path, CANONICAL_MASS_PREFIX)


def _normalize_legacy_source_path(path: str) -> tuple[str, bool]:
    clean = str(path or "").strip()
    if not _is_prefixed_path(clean, LEGACY_MASS_PREFIX):
        return clean, False
    suffix = clean.removeprefix(LEGACY_MASS_PREFIX)
    candidate = f"{CANONICAL_MASS_PREFIX}{suffix}"
    legacy_exists = os.path.exists(clean)
    legacy_is_mounted = os.path.ismount(LEGACY_MASS_PREFIX)
    candidate_exists = os.path.exists(candidate)
    if candidate_exists and (not legacy_exists or not legacy_is_mounted):
        return candidate, True
    return clean, False


def _path_usage(path: str, expect_separate_mount: bool = False) -> dict[str, Any]:
    exists = os.path.exists(path)
    readable = os.access(path, os.R_OK) if exists else False
    writable = os.access(path, os.W_OK) if exists else False
    if not exists:
        return {
            "path": path,
            "exists": False,
            "readable": False,
            "writable": False,
            "mount_point": None,
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "used_percent": None,
            "mount_expected": bool(expect_separate_mount),
            "mount_ok": False if expect_separate_mount else True,
        }

    try:
        stats = os.statvfs(path)
        total = stats.f_blocks * stats.f_frsize
        free = stats.f_bavail * stats.f_frsize
        used = total - free
        used_percent = round((used / total) * 100, 1) if total > 0 else 0.0
        mount_point = _get_mount_point(path)
        mount_ok = mount_point != "/" if expect_separate_mount else True
        return {
            "path": path,
            "exists": True,
            "readable": readable,
            "writable": writable,
            "mount_point": mount_point,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "used_percent": used_percent,
            "mount_expected": bool(expect_separate_mount),
            "mount_ok": mount_ok,
        }
    except OSError:
        mount_point = _get_mount_point(path)
        mount_ok = mount_point != "/" if expect_separate_mount else True
        return {
            "path": path,
            "exists": True,
            "readable": readable,
            "writable": writable,
            "mount_point": mount_point,
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "used_percent": None,
            "mount_expected": bool(expect_separate_mount),
            "mount_ok": mount_ok,
        }


def _df_usage() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    try:
        out = subprocess.run(["df", "-B1", "-P"], capture_output=True, text=True, timeout=10)
        if out.returncode != 0 or not out.stdout:
            return result
        lines = out.stdout.strip().split("\n")
        if len(lines) < 2:
            return result
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
            fs = parts[0]
            mount = " ".join(parts[5:]) if len(parts) > 5 else ""
            try:
                total = int(parts[1])
                used = int(parts[2])
                free = int(parts[3])
                used_pct = float(parts[4].rstrip("%")) if parts[4].rstrip("%") else None
            except Exception:
                continue
            result.append(
                {
                    "filesystem": fs,
                    "mount_point": mount,
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "used_percent": used_pct,
                }
            )
    except Exception:
        pass
    return result


def _zfs_diagnostics(pool: str | None) -> dict[str, Any]:
    if not pool:
        return {
            "available": False,
            "pool": None,
            "health": None,
            "status_ok": None,
            "status_summary": "No ZFS pool configured.",
            "errors": [],
            "command_error": None,
            "used_bytes": None,
            "avail_bytes": None,
            "mount_point": None,
        }
    if not shutil_which("zpool") or not shutil_which("zfs"):
        return {
            "available": False,
            "pool": pool,
            "health": None,
            "status_ok": None,
            "status_summary": None,
            "errors": [],
            "command_error": "zpool/zfs command not available in runtime.",
            "used_bytes": None,
            "avail_bytes": None,
            "mount_point": None,
        }

    out = {
        "available": True,
        "pool": pool,
        "health": None,
        "status_ok": None,
        "status_summary": None,
        "errors": [],
        "command_error": None,
        "used_bytes": None,
        "avail_bytes": None,
        "mount_point": None,
    }
    try:
        proc = subprocess.run(["zpool", "status", pool], capture_output=True, text=True, timeout=8)
        full = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        for line in full.splitlines():
            stripped = line.strip()
            if stripped.startswith("state:"):
                out["health"] = stripped.removeprefix("state:").strip()
            if stripped.startswith("errors:"):
                msg = stripped.removeprefix("errors:").strip()
                if msg and msg.lower() != "no known data errors":
                    out["errors"].append(msg)

        proc_x = subprocess.run(["zpool", "status", "-x", pool], capture_output=True, text=True, timeout=8)
        status_x = (proc_x.stdout or "").strip()
        if status_x:
            out["status_summary"] = status_x
            out["status_ok"] = "is healthy" in status_x.lower()
        zfs_proc = subprocess.run(
            ["zfs", "list", "-Hp", "-o", "used,avail,mountpoint", pool], capture_output=True, text=True, timeout=8
        )
        if zfs_proc.returncode == 0 and zfs_proc.stdout.strip():
            parts = zfs_proc.stdout.splitlines()[0].split("\t")
            if len(parts) >= 3:
                out["used_bytes"] = int(parts[0]) if parts[0].isdigit() else None
                out["avail_bytes"] = int(parts[1]) if parts[1].isdigit() else None
                out["mount_point"] = parts[2].strip()
    except Exception as exc:
        out["command_error"] = str(exc)
    return out


def shutil_which(cmd: str) -> bool:
    from shutil import which

    return which(cmd) is not None


@dataclass
class RuntimeState:
    process: subprocess.Popen[str] | None = None
    run_thread: threading.Thread | None = None
    running: bool = False
    stop_requested: bool = False
    run_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    active_step: str | None = None
    progress_current: int = 0
    progress_total: int = 0
    progress_line: str | None = None
    _run_lock_fd: Any | None = None


@dataclass
class ScheduleState:
    enabled: bool = True
    time_of_day: str = "02:00"
    next_run_at: datetime | None = None
    last_triggered_at: datetime | None = None


_state = RuntimeState()
_schedule = ScheduleState()
_lock = threading.Lock()
_scheduler_stop = threading.Event()
_scheduler_lock_fd = None
_schedule_loaded = False


def _load_custodian_seed() -> dict[str, Any]:
    fallback = {
        "version": 1,
        "backup_pool": "mass",
        "rsync_bwlimit": "20M",
        "sleep_seconds": 5,
        "exclude_hidden": True,
        "excludes": list(DEFAULT_RSYNC_EXCLUDES),
        "targets": [
            {"id": _new_target_id(), "profile": t["profile"], "source": t["source"], "destination": t["destination"], "enabled": True}
            for t in DEFAULT_EXTERNAL_TARGETS
        ],
    }
    configured = os.getenv("CUSTODIAN_CONFIG_PATH", "/host/custodian/config.py")
    candidates = [
        Path(configured),
        Path("/host/custodian/config_server.py"),
        Path("/host/custodian/config_office.py"),
        Path("/home/andy/custodian/config.py"),
    ]
    custodian_path = next((p for p in candidates if p.exists()), None)
    if custodian_path is None:
        return fallback
    try:
        spec = importlib.util.spec_from_file_location("custodian_seed", str(custodian_path))
        if spec is None or spec.loader is None:
            return fallback
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        backup_cfg = getattr(module, "BACKUP_CONFIG", {}) or {}
        targets = []
        excludes: list[str] = []
        for profile, cfg in backup_cfg.items():
            dest = str(cfg.get("dest", "")).strip()
            for ex in cfg.get("excludes", []) or []:
                ex_str = str(ex).strip()
                if ex_str:
                    excludes.append(ex_str)
            for source in cfg.get("dirs", []) or []:
                source_str = str(source).strip()
                if source_str and dest:
                    targets.append(
                        {
                            "id": _new_target_id(),
                            "profile": str(profile),
                            "source": source_str,
                            "destination": dest,
                            "enabled": True,
                        }
                    )
        if not targets:
            targets = fallback["targets"]
        return {
            "version": 1,
            "backup_pool": getattr(module, "BACKUP_POOL", "mass"),
            "rsync_bwlimit": getattr(module, "RSYNC_BWLIMIT", "20M"),
            "sleep_seconds": int(getattr(module, "BACKUP_SLEEP_SECONDS", 5)),
            "exclude_hidden": True,
            "excludes": sorted(set(DEFAULT_RSYNC_EXCLUDES + excludes)),
            "targets": targets,
        }
    except Exception:
        return fallback


def _seed_backup_config_if_needed() -> None:
    if BACKUP_CONFIG_FILE.exists():
        return
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    seed = _load_custodian_seed()
    BACKUP_CONFIG_FILE.write_text(json.dumps(seed, indent=2), encoding="utf-8")


def _load_backup_config() -> dict[str, Any]:
    _seed_backup_config_if_needed()
    try:
        data = json.loads(BACKUP_CONFIG_FILE.read_text(encoding="utf-8"))
        targets = data.get("targets") if isinstance(data.get("targets"), list) else []
        clean_targets = []
        config_changed = False
        for t in targets:
            source = str(t.get("source") or "").strip()
            normalized_source, source_changed = _normalize_legacy_source_path(source)
            if source_changed:
                config_changed = True
            clean_targets.append(
                {
                    "id": str(t.get("id") or _new_target_id()),
                    "profile": str(t.get("profile") or "default"),
                    "source": normalized_source,
                    "destination": str(t.get("destination") or "").strip(),
                    "enabled": bool(t.get("enabled", True)),
                }
            )
        normalized = {
            "version": int(data.get("version", 1)),
            "backup_pool": data.get("backup_pool"),
            "rsync_bwlimit": data.get("rsync_bwlimit"),
            "sleep_seconds": int(data.get("sleep_seconds", 5)),
            "exclude_hidden": bool(data.get("exclude_hidden", True)),
            "excludes": [str(x).strip() for x in (data.get("excludes") or []) if str(x).strip()],
            "targets": [t for t in clean_targets if t["source"] and t["destination"]],
        }
        if config_changed:
            _save_backup_config(normalized)
        return normalized
    except Exception:
        seed = _load_custodian_seed()
        _save_backup_config(seed)
        return seed


def _save_backup_config(config: dict[str, Any]) -> None:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    BACKUP_CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def list_backup_targets() -> list[dict[str, Any]]:
    return _load_backup_config()["targets"]


def add_backup_target(profile: str, source: str, destination: str, enabled: bool = True) -> dict[str, Any]:
    config = _load_backup_config()
    normalized_source, _ = _normalize_legacy_source_path(str(source or "").strip())
    item = {
        "id": _new_target_id(),
        "profile": str(profile or "default"),
        "source": normalized_source,
        "destination": str(destination or "").strip(),
        "enabled": bool(enabled),
    }
    if not item["source"] or not item["destination"]:
        raise ValueError("source and destination are required")
    config["targets"].append(item)
    _save_backup_config(config)
    return item


def update_backup_target(target_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    config = _load_backup_config()
    for target in config["targets"]:
        if target["id"] != target_id:
            continue
        if "profile" in payload:
            target["profile"] = str(payload.get("profile") or "default")
        if "source" in payload:
            normalized_source, _ = _normalize_legacy_source_path(str(payload.get("source") or "").strip())
            target["source"] = normalized_source
        if "destination" in payload:
            target["destination"] = str(payload.get("destination") or "").strip()
        if "enabled" in payload:
            target["enabled"] = bool(payload.get("enabled"))
        if not target["source"] or not target["destination"]:
            raise ValueError("source and destination are required")
        _save_backup_config(config)
        return target
    raise FileNotFoundError(target_id)


def delete_backup_target(target_id: str) -> None:
    config = _load_backup_config()
    before = len(config["targets"])
    config["targets"] = [t for t in config["targets"] if t["id"] != target_id]
    if len(config["targets"]) == before:
        raise FileNotFoundError(target_id)
    _save_backup_config(config)


def _save_schedule_state() -> None:
    payload = {
        "enabled": _schedule.enabled,
        "time_of_day": _schedule.time_of_day,
        "next_run_at": _iso(_schedule.next_run_at),
        "last_triggered_at": _iso(_schedule.last_triggered_at),
    }
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        SCHEDULE_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _load_schedule_state() -> None:
    if SCHEDULE_STATE_FILE.exists():
        try:
            payload = json.loads(SCHEDULE_STATE_FILE.read_text(encoding="utf-8"))
            _schedule.enabled = bool(payload.get("enabled", True))
            _schedule.time_of_day = str(payload.get("time_of_day", "02:00"))
            _parse_hhmm(_schedule.time_of_day)
            next_run_raw = payload.get("next_run_at")
            if isinstance(next_run_raw, str) and next_run_raw:
                _schedule.next_run_at = datetime.fromisoformat(next_run_raw.replace("Z", "+00:00"))
            last_raw = payload.get("last_triggered_at")
            if isinstance(last_raw, str) and last_raw:
                _schedule.last_triggered_at = datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
            return
        except Exception:
            pass
    _schedule.enabled = True
    _schedule.time_of_day = "02:00"
    _schedule.next_run_at = _compute_next_run(datetime.now(timezone.utc), _schedule.time_of_day)
    _schedule.last_triggered_at = None
    _save_schedule_state()


def _latest_runs(limit: int = 10) -> list[dict[str, Any]]:
    if not RUNS_DIR.exists():
        return []
    run_dirs = [path for path in RUNS_DIR.iterdir() if path.is_dir() and path.name.startswith("run_")]
    run_dirs.sort(key=lambda path: path.name, reverse=True)
    out = []
    for run_dir in run_dirs[:limit]:
        main_log = run_dir / "main.log"
        debug_log = run_dir / "debug.log"
        last_line = _tail(main_log, lines=1).strip() if main_log.exists() else ""
        summary = _read_run_summary(run_dir)
        out.append(
            {
                "run_id": run_dir.name,
                "started_at": run_dir.name.removeprefix("run_"),
                "main_log_path": str(main_log),
                "debug_log_path": str(debug_log),
                "last_line": (summary or {}).get("last_line") or last_line or None,
                "finished_at": (summary or {}).get("finished_at"),
                "status": (summary or {}).get("status"),
                "archive_ok": (summary or {}).get("archive_ok"),
                "sync_total": (summary or {}).get("sync_total"),
                "sync_failed": (summary or {}).get("sync_failed"),
            }
        )
    return out


def _target_history_index(limit_runs: int = 200) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for run in _latest_runs(limit=limit_runs):
        run_dir = Path(run["main_log_path"]).parent
        summary = _read_run_summary(run_dir)
        if not summary:
            continue
        run_id = str(summary.get("run_id") or run.get("run_id") or "")
        finished_at = summary.get("finished_at")
        sync_results = summary.get("sync_results") or []
        if not isinstance(sync_results, list):
            continue
        for item in sync_results:
            if not isinstance(item, dict):
                continue
            profile = str(item.get("profile") or "default")
            source = str(item.get("source") or "").strip()
            destination = str(item.get("destination") or "").strip()
            if not source or not destination:
                continue
            key = f"{profile}|{source}|{destination}"
            slot = index.setdefault(
                key,
                {
                    "last_attempt_at": None,
                    "last_attempt_run_id": None,
                    "last_attempt_ok": None,
                    "last_attempt_exit_code": None,
                    "last_backup_at": None,
                    "last_backup_run_id": None,
                },
            )
            if slot["last_attempt_at"] is None:
                slot["last_attempt_at"] = finished_at
                slot["last_attempt_run_id"] = run_id or None
                slot["last_attempt_ok"] = bool(item.get("ok"))
                slot["last_attempt_exit_code"] = item.get("exit_code")
            if slot["last_backup_at"] is None and bool(item.get("ok")) and finished_at:
                slot["last_backup_at"] = finished_at
                slot["last_backup_run_id"] = run_id or None
    return index


def _snapshot_history(limit: int = 40) -> list[dict[str, Any]]:
    out = []
    for run in _latest_runs(limit=40):
        run_dir = Path(run["main_log_path"]).parent
        lines = _tail(run_dir / "main.log", lines=400).splitlines()
        for line in lines:
            if "snapshot" not in line.lower():
                continue
            out.append({"name": line.strip(), "timestamp": run["started_at"], "source": "run-log", "run_id": run["run_id"]})
            if len(out) >= limit:
                return out[:limit]
    return out[:limit]


def _backup_files(limit: int = 20) -> list[dict[str, Any]]:
    if not BACKUP_ROOT.exists():
        return []
    files = sorted(BACKUP_ROOT.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for path in files[:limit]:
        try:
            stat = path.stat()
            out.append(
                {
                    "name": path.name,
                    "bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        except OSError:
            continue
    return out


def _target_health(profile: str, source: str, destination: str) -> dict[str, Any]:
    source_exists = os.path.exists(source)
    source_readable = os.access(source, os.R_OK) if source_exists else False
    source_mount_point = _get_mount_point(source) if source_exists else None
    source_mount_required = _requires_separate_mount(source)
    source_mount_ok = bool(source_exists and source_mount_point and source_mount_point != "/") if source_mount_required else source_exists
    destination_exists = os.path.exists(destination)
    destination_writable = os.access(destination, os.W_OK) if destination_exists else False
    destination_mount_point = _get_mount_point(destination) if destination_exists else None
    destination_mount_required = True
    destination_mount_ok = bool(destination_exists and destination_mount_point and destination_mount_point != "/")
    ready = all([source_exists, source_readable, source_mount_ok, destination_exists, destination_writable, destination_mount_ok])
    return {
        "profile": profile,
        "source": source,
        "destination": destination,
        "source_exists": source_exists,
        "source_readable": source_readable,
        "source_mount_point": source_mount_point,
        "source_mount_required": source_mount_required,
        "source_mount_ok": source_mount_ok,
        "destination_exists": destination_exists,
        "destination_writable": destination_writable,
        "destination_mount_point": destination_mount_point,
        "destination_mount_required": destination_mount_required,
        "destination_mount_ok": destination_mount_ok,
        "destination_separate_mount": destination_mount_ok,
        "ready": ready,
    }


def get_backup_overview() -> dict[str, Any]:
    global _schedule_loaded
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _seed_backup_config_if_needed()
    if not _schedule_loaded:
        _load_schedule_state()
        _schedule_loaded = True

    with _lock:
        if _schedule.enabled and _schedule.next_run_at is None:
            _schedule.next_run_at = _compute_next_run(datetime.now(timezone.utc), _schedule.time_of_day)
            _save_schedule_state()

    cfg = _load_backup_config()
    target_mappings = cfg["targets"]
    target_history = _target_history_index(limit_runs=200)
    target_health = []
    for target in target_mappings:
        item = _target_health(target["profile"], target["source"], target["destination"])
        history = target_history.get(f"{target['profile']}|{target['source']}|{target['destination']}") or {}
        item["last_backup_at"] = history.get("last_backup_at")
        item["last_backup_run_id"] = history.get("last_backup_run_id")
        item["last_attempt_at"] = history.get("last_attempt_at")
        item["last_attempt_ok"] = history.get("last_attempt_ok")
        item["last_attempt_exit_code"] = history.get("last_attempt_exit_code")
        target_health.append(item)
    source_paths = sorted({t["source"] for t in target_mappings})
    destination_paths = sorted({t["destination"] for t in target_mappings})
    storage_diagnostics = {
        "sources": [_path_usage(path, expect_separate_mount=_requires_separate_mount(path)) for path in source_paths],
        "destinations": [_path_usage(path, expect_separate_mount=True) for path in destination_paths],
        "filesystems": _df_usage(),
        "zfs": _zfs_diagnostics(cfg.get("backup_pool")),
    }

    with _lock:
        running = bool(_state.running)
        status = {
            "running": running,
            "pid": _state.process.pid if running and _state.process else None,
            "run_id": _state.run_id,
            "started_at": _iso(_state.started_at),
            "finished_at": _iso(_state.finished_at),
            "exit_code": _state.exit_code,
            "active_step": _state.active_step,
            "progress_current": _state.progress_current,
            "progress_total": _state.progress_total,
            "progress_line": _state.progress_line,
        }
        schedule = {
            "enabled": _schedule.enabled,
            "time_of_day": _schedule.time_of_day,
            "timezone": "utc",
            "next_run_at": _iso(_schedule.next_run_at),
            "last_triggered_at": _iso(_schedule.last_triggered_at),
        }

    return {
        "status": status,
        "backup_pool": cfg.get("backup_pool"),
        "rsync_bwlimit": cfg.get("rsync_bwlimit"),
        "sleep_seconds": cfg.get("sleep_seconds"),
        "exclude_hidden": bool(cfg.get("exclude_hidden", True)),
        "excludes": [x for x in (cfg.get("excludes") or []) if isinstance(x, str)],
        "targets": [t["source"] for t in target_mappings],
        "target_mappings": target_mappings,
        "target_health": target_health,
        "storage_ready": all(item["ready"] for item in target_health) if target_health else False,
        "storage_diagnostics": storage_diagnostics,
        "timer_schedule": "daily",
        "schedule": schedule,
        "snapshots": _snapshot_history(),
        "recent_runs": _latest_runs(),
        "backup_files": _backup_files(),
    }


def _release_run_lock() -> None:
    with _lock:
        fd = _state._run_lock_fd
        _state._run_lock_fd = None
    try:
        if fd is not None:
            fd.close()
    except Exception:
        pass


def _run_subprocess_with_logs(
    command: list[str], main_log_path: Path, debug_log_path: Path, progress_prefix: str
) -> tuple[int, str | None]:
    _append_log(debug_log_path, "$ " + " ".join(command))
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    last_line = None
    with _lock:
        _state.process = proc
    for raw in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
        line = raw.strip()
        if not line:
            continue
        last_line = line
        _append_log(main_log_path, line)
        with _lock:
            _state.progress_line = f"{progress_prefix}: {line[:240]}"
    proc.wait()
    with _lock:
        if _state.process is proc:
            _state.process = None
    return proc.returncode, last_line


def _build_rsync_excludes(config: dict[str, Any]) -> list[str]:
    excludes = [x for x in (config.get("excludes") or []) if isinstance(x, str) and x.strip()]
    if config.get("exclude_hidden", True):
        excludes.extend(["--exclude=.*", "--exclude=*/.*"])
    merged = list(DEFAULT_RSYNC_EXCLUDES)
    for item in excludes:
        if item not in merged:
            merged.append(item)
    return merged


def _run_backup_job(
    run_id: str,
    run_dir: Path,
    config: dict[str, Any],
    backup_name: str,
    backup_path: Path | None,
    selected_targets: list[dict[str, Any]] | None = None,
    include_archive: bool = True,
    trigger: str = "manual",
) -> None:
    main_log_path = run_dir / "main.log"
    debug_log_path = run_dir / "debug.log"
    if selected_targets is None:
        enabled_targets = [t for t in config.get("targets", []) if t.get("enabled", True)]
    else:
        enabled_targets = selected_targets
    total_steps = (1 if include_archive else 0) + len(enabled_targets)
    summary: dict[str, Any] = {
        "run_id": run_id,
        "started_at": _iso(datetime.now(timezone.utc)),
        "finished_at": None,
        "status": "running",
        "archive_ok": include_archive is False,
        "archive_file": backup_name,
        "archive_error": None,
        "run_type": trigger,
        "include_archive": bool(include_archive),
        "sync_total": len(enabled_targets),
        "sync_ok": 0,
        "sync_failed": 0,
        "sync_results": [],
        "snapshot_status": "skipped",
        "snapshot_name": None,
        "snapshot_error": None,
        "last_line": None,
        "errors": [],
    }
    _write_run_summary(run_dir, summary)
    _append_log(main_log_path, f"[{run_id}] backup run started")

    run_failed = False
    try:
        with _lock:
            _state.running = True
            _state.active_step = "archive" if include_archive else "sync"
            _state.progress_current = 0
            _state.progress_total = max(total_steps, 1)
            _state.progress_line = f"Starting archive {backup_name}" if include_archive else "Starting target sync steps"

        if include_archive:
            tar_cmd = [
                "tar",
                "--warning=no-file-changed",
                "--ignore-failed-read",
                "--checkpoint=500",
                "--checkpoint-action=echo=archive checkpoint %u",
                "-czf",
                str(backup_path),
                "-C",
                "/data",
                "milvus",
                "etcd",
                "minio",
            ]
            rc, last_line = _run_subprocess_with_logs(tar_cmd, main_log_path, debug_log_path, "archive")
            summary["last_line"] = last_line
            if rc == 0:
                summary["archive_ok"] = True
                _append_log(main_log_path, "Archive step completed.")
            else:
                run_failed = True
                summary["archive_error"] = f"tar exited with code {rc}"
                summary["errors"].append(summary["archive_error"])
                _append_log(main_log_path, f"Archive step failed: {summary['archive_error']}")
        else:
            summary["archive_ok"] = True
            summary["archive_file"] = None
            summary["archive_error"] = "archive skipped for target-only backup"

        with _lock:
            _state.progress_current = 1 if include_archive else 0
            _state.active_step = "sync"
            _state.progress_line = "Starting target sync steps"

        excludes = _build_rsync_excludes(config)
        if enabled_targets and not shutil_which("rsync"):
            run_failed = True
            summary["sync_failed"] = len(enabled_targets)
            summary["errors"].append("rsync is not available in runtime.")
            summary["status"] = "failed"
            summary["last_line"] = "rsync is not available in runtime."
            _append_log(main_log_path, "Sync step failed: rsync is not available in runtime.")
            enabled_targets = []
        for idx, target in enumerate(enabled_targets, start=1):
            with _lock:
                if _state.stop_requested:
                    raise RuntimeError("Backup stop requested by user.")
            src = str(target.get("source", "")).strip().rstrip("/")
            dst_root = str(target.get("destination", "")).strip()
            if not src or not dst_root:
                continue
            dst = os.path.join(dst_root, os.path.basename(src))
            rsync_cmd = [
                "rsync",
                "-aAH",
                "--delete",
                "--human-readable",
                "--info=progress2",
                f"--bwlimit={config.get('rsync_bwlimit') or '20M'}",
            ] + excludes + [f"{src}/", dst]

            _append_log(main_log_path, f"Syncing {src} -> {dst}")
            rc, last_line = _run_subprocess_with_logs(rsync_cmd, main_log_path, debug_log_path, f"sync:{src}")
            item = {
                "profile": target.get("profile"),
                "source": src,
                "destination": dst_root,
                "dest_path": dst,
                "exit_code": rc,
                "ok": rc == 0,
                "last_line": last_line,
            }
            summary["sync_results"].append(item)
            summary["last_line"] = last_line or summary["last_line"]
            if rc == 0:
                summary["sync_ok"] += 1
                _append_log(main_log_path, f"Sync completed for {src}")
            else:
                run_failed = True
                summary["sync_failed"] += 1
                err = f"Sync failed for {src} with exit code {rc}"
                summary["errors"].append(err)
                _append_log(main_log_path, err)
            with _lock:
                _state.progress_current = (1 if include_archive else 0) + idx
                _state.progress_line = f"Completed {idx}/{len(enabled_targets)} sync targets"
            _write_run_summary(run_dir, summary)
            time.sleep(max(int(config.get("sleep_seconds", 5)), 0))

        pool = str(config.get("backup_pool") or "").strip()
        if include_archive and pool and shutil_which("zfs"):
            snapshot_name = f"after_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            summary["snapshot_name"] = snapshot_name
            with _lock:
                _state.active_step = "snapshot"
                _state.progress_line = f"Creating snapshot {pool}@{snapshot_name}"
            snap_cmd = ["zfs", "snapshot", f"{pool}@{snapshot_name}"]
            rc, last_line = _run_subprocess_with_logs(snap_cmd, main_log_path, debug_log_path, "snapshot")
            summary["last_line"] = last_line or summary["last_line"]
            if rc == 0:
                summary["snapshot_status"] = "ok"
            else:
                summary["snapshot_status"] = "failed"
                summary["snapshot_error"] = f"zfs snapshot exited with code {rc}"
                summary["errors"].append(summary["snapshot_error"])
        elif include_archive:
            summary["snapshot_status"] = "skipped"
            summary["snapshot_error"] = "zfs command unavailable in runtime"
        else:
            summary["snapshot_status"] = "skipped"
            summary["snapshot_error"] = "snapshot skipped for target-only backup"

        if summary["sync_failed"] > 0 or not summary["archive_ok"] or summary["snapshot_status"] == "failed":
            summary["status"] = "failed" if run_failed else "partial"
            exit_code = 1
        else:
            summary["status"] = "ok"
            exit_code = 0
    except RuntimeError as exc:
        summary["status"] = "cancelled"
        summary["errors"].append(str(exc))
        summary["last_line"] = str(exc)
        exit_code = 130
        _append_log(main_log_path, str(exc))
    except Exception as exc:
        summary["status"] = "failed"
        summary["errors"].append(str(exc))
        summary["last_line"] = str(exc)
        exit_code = 1
        _append_log(main_log_path, f"Unhandled backup error: {exc}")
    finally:
        summary["finished_at"] = _iso(datetime.now(timezone.utc))
        _write_run_summary(run_dir, summary)
        with _lock:
            _state.running = False
            _state.stop_requested = False
            _state.run_thread = None
            _state.process = None
            _state.finished_at = datetime.now(timezone.utc)
            _state.exit_code = exit_code
            _state.active_step = None
            _state.progress_line = summary.get("last_line") or f"Backup finished with status {summary['status']}"
        _release_run_lock()


def start_backup(
    target_ids: list[str] | None = None,
    include_archive: bool = True,
    trigger: str = "manual",
) -> dict[str, Any]:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    config = _load_backup_config()
    selected_targets: list[dict[str, Any]] | None = None
    if target_ids is not None:
        requested_ids = {str(target_id).strip() for target_id in target_ids if str(target_id).strip()}
        if not requested_ids:
            raise ValueError("target_ids must include at least one target id")
        selected_targets = [t for t in config.get("targets", []) if t.get("id") in requested_ids]
        found_ids = {str(t.get("id")) for t in selected_targets}
        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise FileNotFoundError(", ".join(sorted(missing_ids)))
    with _lock:
        if _state.running:
            raise RuntimeError("Backup is already running.")
    run_lock_fd = _acquire_lock(RUN_LOCK_FILE)
    if run_lock_fd is None:
        raise RuntimeError("Another worker is already running a backup.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{stamp}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    backup_name = f"milvus_volumes_{stamp}.tar.gz" if include_archive else ""
    backup_path = BACKUP_ROOT / backup_name if include_archive else None
    progress_targets = selected_targets if selected_targets is not None else [t for t in config["targets"] if t.get("enabled", True)]
    with _lock:
        _state.process = None
        _state.run_thread = None
        _state.running = True
        _state.stop_requested = False
        _state.run_id = run_id
        _state.started_at = datetime.now(timezone.utc)
        _state.finished_at = None
        _state.exit_code = None
        _state.active_step = "archive" if include_archive else "sync"
        _state.progress_current = 0
        _state.progress_total = max((1 if include_archive else 0) + len(progress_targets), 1)
        _state.progress_line = f"Backup started: {backup_name}" if include_archive else "Target backup started."
        _state._run_lock_fd = run_lock_fd

    worker = threading.Thread(
        target=_run_backup_job,
        args=(run_id, run_dir, config, backup_name, backup_path, selected_targets, include_archive, trigger),
        daemon=True,
        name="backup-runner",
    )
    with _lock:
        _state.run_thread = worker
    worker.start()
    return get_backup_overview()


def start_target_backup(target_id: str) -> dict[str, Any]:
    clean_id = str(target_id or "").strip()
    if not clean_id:
        raise ValueError("target_id is required")
    return start_backup(target_ids=[clean_id], include_archive=False, trigger="target")


def stop_backup() -> dict[str, Any]:
    thread = None
    proc = None
    with _lock:
        if not _state.running:
            raise RuntimeError("No running backup process found.")
        _state.stop_requested = True
        _state.progress_line = "Stop requested. Waiting for current step to end..."
        proc = _state.process
        thread = _state.run_thread
    if proc is not None and proc.poll() is None:
        try:
            proc.send_signal(signal.SIGTERM)
        except Exception:
            pass
    if thread is not None:
        thread.join(timeout=10)
    return get_backup_overview()


def get_run_logs(run_id: str, tail_lines: int = 180) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(run_id)
    summary = _read_run_summary(run_dir)
    return {
        "main_log_tail": _tail(run_dir / "main.log", lines=tail_lines),
        "debug_log_tail": _tail(run_dir / "debug.log", lines=tail_lines),
        "summary": summary,
    }


def update_schedule(enabled: bool, time_of_day: str) -> dict[str, Any]:
    _parse_hhmm(time_of_day)
    now = datetime.now(timezone.utc)
    with _lock:
        _schedule.enabled = bool(enabled)
        _schedule.time_of_day = time_of_day
        _schedule.next_run_at = _compute_next_run(now, time_of_day) if enabled else None
        _save_schedule_state()
    return get_backup_overview()


def _schedule_worker() -> None:
    while not _scheduler_stop.is_set():
        try:
            now = datetime.now(timezone.utc)
            with _lock:
                due = _schedule.enabled and _schedule.next_run_at is not None and _schedule.next_run_at <= now
            if due:
                try:
                    start_backup()
                    with _lock:
                        _schedule.last_triggered_at = now
                        _schedule.next_run_at = _compute_next_run(now, _schedule.time_of_day)
                        _save_schedule_state()
                except Exception:
                    pass
        finally:
            _scheduler_stop.wait(30)


def start_scheduler_best_effort() -> None:
    global _scheduler_lock_fd
    global _schedule_loaded
    if _scheduler_lock_fd is not None:
        return
    _scheduler_lock_fd = _acquire_lock(SCHEDULER_LOCK_FILE)
    if _scheduler_lock_fd is None:
        return
    _load_schedule_state()
    _schedule_loaded = True
    thread = threading.Thread(target=_schedule_worker, daemon=True, name="backup-scheduler")
    thread.start()

