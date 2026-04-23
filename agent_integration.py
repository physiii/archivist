from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests


_DEFAULT_AGENT_IDS = (
    "archivist-main",
    "archivist-health",
    "archivist-repair",
    "archivist-observer",
    "archivist-verifier",
)

_AGENT_DOC_FILES = (
    "IDENTITY.md",
    "SOUL.md",
    "AGENTS.md",
    "TOOLS.md",
    "USER.md",
    "HEARTBEAT.md",
    "MEMORY.md",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def team_root() -> Path:
    return repo_root() / "openclaw-team"


def host_workspace() -> str:
    explicit = (os.getenv("ARCHIVIST_HOST_WORKSPACE") or "").strip()
    if explicit:
        return explicit
    local = str(repo_root())
    if local == "/app":
        return "/home/andy/archivist"
    return local


def console_agent_id() -> str:
    return (os.getenv("ARCHIVIST_OPENCLAW_CONSOLE_AGENT_ID") or "archivist-main").strip() or "archivist-main"


def visible_agent_ids() -> list[str]:
    raw = (os.getenv("ARCHIVIST_OPENCLAW_VISIBLE_AGENT_IDS") or "").strip()
    if raw:
        return _dedupe([part.strip() for part in raw.split(",")])
    return list(_DEFAULT_AGENT_IDS)


def default_web_session_key(agent_id: str | None = None) -> str:
    aid = (agent_id or console_agent_id()).strip() or console_agent_id()
    return f"main:web:{uuid.uuid4().hex[:12]}@{aid}"


def encode_session_ref(agent_id: str, session_key: str) -> str:
    safe_agent = (agent_id or console_agent_id()).strip() or console_agent_id()
    safe_key = (session_key or "").strip() or default_web_session_key(safe_agent)
    return f"agent:{safe_agent}:{safe_key}"


def gateway_session_key(agent_id: str, session_key: str) -> str:
    return encode_session_ref(agent_id, session_key)


def decode_session_ref(session_ref: str | None) -> tuple[str, str]:
    raw = (session_ref or "").strip()
    if raw.startswith("agent:"):
        parts = raw.split(":", 2)
        if len(parts) == 3 and parts[1].strip() and parts[2].strip():
            return parts[1].strip(), parts[2].strip()
    if raw:
        return console_agent_id(), raw
    aid = console_agent_id()
    return aid, default_web_session_key(aid)


def session_kind(session_key: str) -> str:
    key = (session_key or "").lower()
    if "repair" in key or "fixer" in key:
        return "repair"
    if "observer" in key:
        return "observer"
    if "verifier" in key:
        return "verifier"
    if "health" in key:
        return "health"
    if "web" in key:
        return "chat"
    return "session"


def load_openclaw_config() -> tuple[dict[str, Any], Path | None]:
    for candidate in _openclaw_config_candidates():
        try:
            if candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8")), candidate
        except Exception:
            continue
    return {}, None


def resolve_gateway_url() -> str:
    explicit = (os.getenv("OPENCLAW_GATEWAY_URL") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    config, _ = load_openclaw_config()
    port = config.get("gateway", {}).get("port", 18789)
    default_host = "host.docker.internal" if str(repo_root()) == "/app" else "127.0.0.1"
    return f"http://{default_host}:{port}"


def resolve_gateway_token() -> str:
    explicit = (os.getenv("OPENCLAW_GATEWAY_TOKEN") or "").strip()
    if explicit:
        return explicit
    config, _ = load_openclaw_config()
    return str(config.get("gateway", {}).get("auth", {}).get("token") or "").strip()


def load_agent_docs(agent_id: str) -> str:
    agent_dir = team_root() / "agents" / agent_id
    parts: list[str] = []
    for filename in _AGENT_DOC_FILES:
        path = agent_dir / filename
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if content:
            parts.append(f"### {filename}\n{content}")
    return "\n\n".join(parts)


def build_agent_system_message(agent_id: str | None = None, screen_context: str = "") -> str:
    aid = (agent_id or console_agent_id()).strip() or console_agent_id()
    project_root = host_workspace()
    agent_dir = f"{project_root}/openclaw-team/agents/{aid}"
    docs = load_agent_docs(aid)
    identity_block = f"\n\n## Agent identity ({aid})\n{docs}" if docs else ""
    return f"""You are Archivist's built-in operator assistant inside a self-hosted archive and media-analysis workspace.

## Runtime environment
- Project name: Archivist
- Project workspace (repo root): {project_root}
- IMPORTANT: The real project workspace is {project_root} and not /app or /home/andy/.openclaw/workspace
- Agent workspace docs: {agent_dir}
- OpenClaw agent id: {aid}
- OpenClaw gateway: {resolve_gateway_url()}

## Product areas
- Collections: Milvus-backed catalog, search, collection detail, embeddings preview
- Backup: target mappings, schedules, logs, replication status
- Indexing: discovery targets, runs, transcript ingestion
- Media: multimodal processing, event ledger, summary artifacts, sidecars
- Console: chat, fleet, system status, agent settings

## Codebase layout
- {project_root}/main.py — Flask API routes and UI serving
- {project_root}/backups_service.py — backup scheduler and logs
- {project_root}/indexing_service.py — indexing scheduler and target management
- {project_root}/media/ — pipeline, recaps, memory, evidence store, composer
- {project_root}/ui/src/ — React UI
- {project_root}/tests/ — pytest and Playwright coverage
- {project_root}/docker-compose.yml — service deployment

## Working rules
1. When asked what workspace you are using, answer with {project_root}
2. Use absolute {project_root}/... paths when discussing files
3. Never claim the project lives at /app
4. Keep answers direct and technical
5. If you need evidence, inspect the actual files or summarize concrete API state
{identity_block}
{screen_context}"""


def inspect_agent_runtime() -> dict[str, Any]:
    gateway_url = resolve_gateway_url()
    token = resolve_gateway_token()
    config, config_path = load_openclaw_config()
    workspace = host_workspace()
    mounted = Path(workspace).exists()
    errors: list[str] = []
    version = None
    available = False
    try:
        response = requests.get(f"{gateway_url}/health", timeout=3)
        if response.ok:
            payload = response.json()
            available = bool(payload.get("ok"))
            version = payload.get("version")
        else:
            errors.append(f"gateway_http_{response.status_code}")
    except Exception as exc:
        errors.append(f"gateway_unreachable:{exc}")
    if not token:
        errors.append("missing_gateway_token")
    if not mounted:
        errors.append("workspace_not_mounted")
    registered = console_agent_id() in registered_agent_ids(config)
    if not registered:
        errors.append("agent_not_registered")
    return {
        "available": available and bool(token) and mounted and registered,
        "backend": "openclaw-gateway" if available else None,
        "binary": gateway_url,
        "version": version,
        "model": f"openclaw/{console_agent_id()}",
        "workspace_path": workspace,
        "workspace_mounted": mounted,
        "console_agent_id": console_agent_id(),
        "config_path": str(config_path) if config_path else None,
        "token_configured": bool(token),
        "registered": registered,
        "errors": errors,
    }


def registered_agent_ids(config: dict[str, Any] | None = None) -> list[str]:
    data = config if config is not None else load_openclaw_config()[0]
    return _dedupe([str(item.get("id") or "").strip() for item in data.get("agents", {}).get("list", []) if isinstance(item, dict)])


def load_team_agents() -> list[dict[str, Any]]:
    agents_dir = team_root() / "agents"
    agents: list[dict[str, Any]] = []
    for manifest in sorted(agents_dir.glob("*/agent-manifest.json")):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        try:
            rel_path = manifest.parent.relative_to(repo_root())
            payload["_path"] = f"{host_workspace()}/{rel_path.as_posix()}"
        except Exception:
            payload["_path"] = str(manifest.parent)
        agents.append(payload)
    agents.sort(key=lambda item: (item.get("ui", {}).get("sort_key", 9999), item.get("name", "")))
    return agents


def load_openclaw_sessions_for_agents(agent_ids: list[str] | None = None) -> list[dict[str, Any]]:
    sessions_by_id: dict[str, dict[str, Any]] = {}
    for agent_id in agent_ids or visible_agent_ids():
        for store_owner, store_path in _session_store_candidates(agent_id):
            if not store_path:
                continue
            try:
                store = json.loads(store_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for session_key, meta in (store or {}).items():
                if not isinstance(meta, dict):
                    continue
                routed_agent_id = _session_agent_id(str(session_key), meta)
                if store_owner in {"main", "default"} and not routed_agent_id:
                    continue
                effective_agent_id = routed_agent_id or agent_id
                if effective_agent_id != agent_id:
                    continue
                session_file = resolve_openclaw_session_file(meta.get("sessionFile"))
                message_count = 0
                last_message = ""
                title = str(session_key)
                if session_file and session_file.is_file():
                    messages = load_openclaw_messages_from_transcript(session_file)
                    if messages:
                        message_count = len(messages)
                        last_message = messages[-1].get("text", "")[:120]
                        user_messages = [m.get("text", "") for m in messages if m.get("role") == "user"]
                        if user_messages:
                            title = user_messages[0][:80]
                session_id = encode_session_ref(effective_agent_id, str(session_key))
                sessions_by_id[session_id] = {
                    "id": session_id,
                    "agentId": effective_agent_id,
                    "sessionKey": str(session_key),
                    "source": "openclaw",
                    "status": str(meta.get("status") or "unknown"),
                    "createdAt": int(meta.get("startedAt") or 0),
                    "updatedAt": int(meta.get("updatedAt") or meta.get("endedAt") or 0),
                    "messageCount": message_count,
                    "lastMessage": last_message,
                    "title": title,
                    "kind": session_kind(str(session_key)),
                    "sessionFile": str(session_file) if session_file else None,
                    "storeOwner": store_owner,
                }
    sessions = list(sessions_by_id.values())
    sessions.sort(key=lambda item: item.get("updatedAt", 0), reverse=True)
    return sessions


def resolve_openclaw_session_file(path_text: str | None) -> Path | None:
    raw = str(path_text or "").strip()
    if not raw:
        return None
    candidates = [
        Path(raw),
        Path(raw.replace("/home/node/.openclaw/", "/host/.openclaw/")),
        Path(raw.replace("/home/andy/.openclaw/", "/host/.openclaw/")),
        Path(raw.replace("/home/node/.openclaw/", str(Path.home() / ".openclaw") + "/")),
        Path(raw.replace("/home/andy/.openclaw/", str(Path.home() / ".openclaw") + "/")),
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return None


def load_openclaw_messages_from_transcript(session_file: Path) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    try:
        for line in session_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            if item.get("type") != "message":
                continue
            message = item.get("message") or {}
            role = str(message.get("role") or "").strip()
            if role == "toolResult":
                text = _extract_message_text(message.get("content"))
                if text:
                    messages.append({"role": "tool", "text": text, "ts": 0, "toolName": message.get("toolName")})
                continue
            if role not in {"user", "assistant", "system"}:
                continue
            text = _extract_message_text(message.get("content"))
            if text:
                messages.append({"role": role, "text": text, "ts": 0})
    except Exception:
        return []
    return messages


def _extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text") or "").strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content or "").strip()


def _openclaw_config_candidates() -> list[Path]:
    explicit = (os.getenv("OPENCLAW_CONFIG_PATH") or "").strip()
    state_dir = (os.getenv("OPENCLAW_STATE_DIR") or "").strip()
    candidates = [
        Path(explicit).expanduser() if explicit else None,
        (Path(state_dir).expanduser() / "openclaw.json") if state_dir else None,
        repo_root() / ".openclaw" / "openclaw.json",
        Path("/host/.openclaw/openclaw.json"),
        Path("/host/openclaw.json"),
        Path.home() / ".openclaw" / "openclaw.json",
        Path("/home/andy/.openclaw/openclaw.json"),
    ]
    out: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        if candidate not in out:
            out.append(candidate)
    return out


def _openclaw_agents_roots() -> list[Path]:
    explicit = (os.getenv("OPENCLAW_AGENTS_DIR") or "").strip()
    state_dir = (os.getenv("OPENCLAW_STATE_DIR") or "").strip()
    candidates = [
        Path(explicit).expanduser() if explicit else None,
        (Path(state_dir).expanduser() / "agents") if state_dir else None,
        repo_root() / ".openclaw" / "agents",
        Path("/host/.openclaw/agents"),
        Path.home() / ".openclaw" / "agents",
        Path("/home/andy/.openclaw/agents"),
    ]
    out: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        if candidate not in out:
            out.append(candidate)
    return out


def _first_readable_session_store(agent_id: str) -> Path | None:
    for root in _openclaw_agents_roots():
        candidate = root / agent_id / "sessions" / "sessions.json"
        try:
            if candidate.is_file():
                return candidate
        except Exception:
            continue
    return None


def _session_store_candidates(agent_id: str) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for owner in (agent_id, "main", "default"):
        store_path = _first_readable_session_store(owner)
        if not store_path or store_path in seen:
            continue
        seen.add(store_path)
        candidates.append((owner, store_path))
    return candidates


def _session_agent_id(session_key: str, meta: dict[str, Any]) -> str | None:
    key = str(session_key or "").strip()
    if "@" in key:
        candidate = key.rsplit("@", 1)[-1].strip()
        if candidate:
            return candidate
    report = meta.get("systemPromptReport") or {}
    report_key = str(report.get("sessionKey") or "").strip()
    if "@" in report_key:
        candidate = report_key.rsplit("@", 1)[-1].strip()
        if candidate:
            return candidate
    return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
