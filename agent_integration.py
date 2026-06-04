from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

import requests


_DEFAULT_AGENT_IDS = (
    "operator-chat",
    "runtime-health-monitor",
    "repair-worker",
    "session-observer",
    "verification-worker",
    "quality-gate",
)

_AGENT_DOC_FILES = (
    "IDENTITY.md",
    "SOUL.md",
    "AGENTS.md",
    "TOOLS.md",
    "USER.md",
    "HEARTBEAT.md",
    "MEMORY.md",
    "OBJECTIVE.md",
    "SKILLS.md",
)

_LANE_ORDER = {
    "system": 0,
    "generic": 1,
    "global": 2,
    "specialist": 3,
}
_LEGACY_RUNTIME_TOKEN = "open" + "claw"


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def agents_repo_root() -> Path:
    explicit = (os.getenv("ARCHIVIST_AGENTS_ROOT") or os.getenv("AGENTS_REPO_ROOT") or "").strip()
    if explicit:
        return Path(explicit).expanduser()
    local = repo_root() / "agents"
    if local.exists():
        return local
    return Path("/media/mass/agents")


def shared_agents_root() -> Path:
    return agents_repo_root() / "agents"


def shared_skills_root() -> Path:
    return agents_repo_root() / "skills"


def shared_mcp_root() -> Path:
    return agents_repo_root() / "mcp"


def host_workspace() -> str:
    explicit = (os.getenv("ARCHIVIST_HOST_WORKSPACE") or "").strip()
    if explicit:
        return explicit
    local = str(repo_root())
    if local == "/app":
        return "/home/andy/archivist"
    return local


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


def _is_legacy_runtime_id(value: str) -> bool:
    return _LEGACY_RUNTIME_TOKEN in str(value or "").lower()


def _scrub_legacy_runtime_text(value: str) -> str:
    return re.sub(_LEGACY_RUNTIME_TOKEN, "agent runtime", str(value or ""), flags=re.IGNORECASE)


def _scrub_legacy_runtime_payload(value: Any) -> Any:
    if isinstance(value, str):
        return _scrub_legacy_runtime_text(value)
    if isinstance(value, list):
        return [_scrub_legacy_runtime_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _scrub_legacy_runtime_payload(item) for key, item in value.items()}
    return value


def _agent_catalog_path() -> Path:
    return shared_agents_root() / "catalog.json"


def load_agent_catalog() -> dict[str, Any]:
    path = _agent_catalog_path()
    try:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _catalog_agent_ids() -> list[str]:
    catalog = load_agent_catalog()
    ids: list[str] = []
    ids.extend(str(item) for item in catalog.get("system_agents") or [])
    ids.extend(str(item) for item in catalog.get("generic_workspace_agents") or [])
    ids.extend(str(item) for item in catalog.get("global_role_briefs") or [])
    domains = catalog.get("specialist_domains") or {}
    if isinstance(domains, dict):
        for values in domains.values():
            if isinstance(values, list):
                ids.extend(str(item) for item in values)
    if not ids and shared_agents_root().is_dir():
        ids.extend(path.name for path in shared_agents_root().iterdir() if path.is_dir() and path.name != "roles")
    return [agent_id for agent_id in _dedupe(ids) if not _is_legacy_runtime_id(agent_id)]


def console_agent_id() -> str:
    configured = (
        os.getenv("ARCHIVIST_AGENT_CONSOLE_AGENT_ID")
        or os.getenv("ARCHIVIST_CONSOLE_AGENT_ID")
        or ""
    ).strip()
    if configured:
        return configured
    ids = _catalog_agent_ids()
    if "operator-chat" in ids:
        return "operator-chat"
    return ids[0] if ids else "operator-chat"


def visible_agent_ids() -> list[str]:
    raw = (
        os.getenv("ARCHIVIST_VISIBLE_AGENT_IDS")
        or os.getenv("ARCHIVIST_AGENT_VISIBLE_IDS")
        or ""
    ).strip()
    if raw:
        return _dedupe([part.strip() for part in raw.split(",")])
    ids = _catalog_agent_ids()
    return ids if ids else list(_DEFAULT_AGENT_IDS)


def default_web_session_key(agent_id: str | None = None) -> str:
    aid = (agent_id or console_agent_id()).strip() or console_agent_id()
    return f"main:web:{uuid.uuid4().hex[:12]}@{aid}"


def encode_session_ref(agent_id: str, session_key: str) -> str:
    safe_agent = (agent_id or console_agent_id()).strip() or console_agent_id()
    safe_key = (session_key or "").strip() or default_web_session_key(safe_agent)
    return f"agent:{safe_agent}:{safe_key}"


def agent_session_key(agent_id: str, session_key: str) -> str:
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
    if "verifier" in key or "verification" in key:
        return "verifier"
    if "health" in key:
        return "health"
    if "web" in key:
        return "chat"
    return "session"


def _agent_dir(agent_id: str) -> Path | None:
    full = shared_agents_root() / agent_id
    if full.is_dir():
        return full
    role = shared_agents_root() / "roles" / f"{agent_id}.md"
    if role.is_file():
        return role
    return None


def load_agent_docs(agent_id: str) -> str:
    target = _agent_dir(agent_id)
    if target is None:
        return ""
    if target.is_file():
        try:
            return target.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    parts: list[str] = []
    for filename in _AGENT_DOC_FILES:
        path = target / filename
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
    agent_target = _agent_dir(aid)
    agent_docs_path = str(agent_target) if agent_target is not None else str(shared_agents_root() / aid)
    docs = load_agent_docs(aid)
    identity_block = f"\n\n## Agent identity ({aid})\n{docs}" if docs else ""
    skill_names = [skill["name"] for skill in load_shared_skills()[:40]]
    skill_block = ", ".join(skill_names)
    mcp_names = [server["name"] for server in load_mcp_servers()[:30]]
    mcp_block = ", ".join(mcp_names)
    return f"""You are Archivist's built-in operator assistant inside a self-hosted archive and media-analysis workspace.

## Runtime environment
- Project name: Archivist
- Project workspace (repo root): {project_root}
- IMPORTANT: The real project workspace is {project_root} and not /app
- Shared agent knowledge base: {agents_repo_root()}
- Agent docs: {agent_docs_path}
- Agent id: {aid}
- Skills available from shared catalog: {skill_block or "none discovered"}
- MCP registry entries: {mcp_block or "none discovered"}

## Product areas
- Collections: Milvus-backed catalog, search, collection detail, embeddings preview
- Backup: target mappings, schedules, logs, replication status
- Indexing: discovery targets, runs, transcript ingestion
- Media: multimodal processing, event ledger, summary artifacts, sidecars
- Console: chat, fleet, system status, agent settings

## Codebase layout
- {project_root}/main.py - Flask API routes and UI serving
- {project_root}/backups_service.py - backup scheduler and logs
- {project_root}/indexing_service.py - indexing scheduler and target management
- {project_root}/media/ - pipeline, recaps, memory, evidence store, composer
- {project_root}/ui/src/ - React UI
- {project_root}/tests/ - pytest and Playwright coverage
- {project_root}/docker-compose.yml - service deployment

## Working rules
1. When asked what workspace you are using, answer with {project_root}
2. Use absolute {project_root}/... paths when discussing files
3. Keep answers direct and technical
4. If you need evidence, inspect actual files or summarize concrete API state
{identity_block}
{screen_context}"""


def _read_manifest(agent_dir: Path, agent_id: str) -> dict[str, Any]:
    manifest_path = agent_dir / "agent-manifest.json"
    if manifest_path.is_file():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"agent_id": agent_id, "id": agent_id}


def _first_heading_or_line(path: Path) -> str:
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip().lstrip("#").strip()
            if line:
                return line
    except Exception:
        pass
    return path.stem.replace("-", " ").replace("_", " ").title()


def _catalog_lane_maps(catalog: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    lanes: dict[str, str] = {}
    groups: dict[str, str] = {}
    for agent_id in catalog.get("system_agents") or []:
        lanes[str(agent_id)] = "system"
        groups[str(agent_id)] = "System"
    for agent_id in catalog.get("generic_workspace_agents") or []:
        lanes[str(agent_id)] = "generic"
        groups[str(agent_id)] = "Generic Workspace"
    for role_id in catalog.get("global_role_briefs") or []:
        lanes[str(role_id)] = "global"
        groups[str(role_id)] = "Global Role Brief"
    domains = catalog.get("specialist_domains") or {}
    if isinstance(domains, dict):
        for domain, values in domains.items():
            if not isinstance(values, list):
                continue
            label = str(domain).replace("_", " ").replace("-", " ").title()
            for agent_id in values:
                lanes[str(agent_id)] = "specialist"
                groups[str(agent_id)] = label
    return lanes, groups


def load_team_agents() -> list[dict[str, Any]]:
    catalog = load_agent_catalog()
    lane_by_id, group_by_id = _catalog_lane_maps(catalog)
    agents: list[dict[str, Any]] = []
    agents_root = shared_agents_root()
    if not agents_root.is_dir():
        return []

    for agent_id in _catalog_agent_ids():
        agent_dir = agents_root / agent_id
        role_file = agents_root / "roles" / f"{agent_id}.md"
        if agent_dir.is_dir():
            payload = _read_manifest(agent_dir, agent_id)
            payload.setdefault("agent_id", payload.get("id") or agent_id)
            payload.setdefault("name", str(payload.get("agent_id") or agent_id).replace("-", " ").replace("_", " ").title())
            identity = agent_dir / "IDENTITY.md"
            if not payload.get("summary") and identity.is_file():
                payload["summary"] = _first_heading_or_line(identity)
            payload["_path"] = str(agent_dir)
            payload["_source"] = "shared-agents"
        elif role_file.is_file():
            payload = {
                "agent_id": agent_id,
                "id": agent_id,
                "name": _first_heading_or_line(role_file),
                "summary": _first_heading_or_line(role_file),
                "_path": str(role_file),
                "_source": "shared-role",
                "role": "global-role-brief",
            }
        else:
            continue
        payload.setdefault("fleet_lane", lane_by_id.get(agent_id, "specialist"))
        payload = _scrub_legacy_runtime_payload(payload)
        payload.setdefault("ui", {})
        if isinstance(payload["ui"], dict):
            payload["ui"].setdefault("badge", group_by_id.get(agent_id, payload.get("fleet_lane", "Agent")))
            payload["ui"]["badge"] = _scrub_legacy_runtime_text(str(payload["ui"].get("badge") or ""))
        agents.append(payload)

    agents.sort(
        key=lambda item: (
            _LANE_ORDER.get(str(item.get("fleet_lane") or "specialist"), 9),
            str((item.get("ui") or {}).get("badge") or ""),
            str(item.get("name") or item.get("agent_id") or ""),
        )
    )
    return agents


def registered_agent_ids(_: dict[str, Any] | None = None) -> list[str]:
    return _dedupe([str(agent.get("agent_id") or agent.get("id") or "") for agent in load_team_agents()])


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    header = text[3:end].strip()
    body = text[end + 4 :].strip()
    data: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def load_shared_skills() -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    root = shared_skills_root()
    if not root.is_dir():
        return skills
    for skill_file in sorted(root.glob("*/SKILL.md")):
        skill_id = skill_file.parent.name
        if skill_id.startswith("_"):
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
        except Exception:
            continue
        meta, body = _parse_frontmatter(text)
        description = meta.get("description") or ""
        if not description:
            for raw in body.splitlines():
                line = raw.strip().lstrip("#").strip()
                if line:
                    description = line
                    break
        skills.append(
            {
                "id": skill_id,
                "name": meta.get("name") or skill_id,
                "description": _scrub_legacy_runtime_text(description),
                "path": str(skill_file),
                "source": "shared-agents",
            }
        )
    return skills


def load_mcp_servers() -> list[dict[str, Any]]:
    registry = shared_mcp_root() / "registry.md"
    servers: list[dict[str, Any]] = []
    if not registry.is_file():
        return servers
    try:
        lines = registry.read_text(encoding="utf-8").splitlines()
    except Exception:
        return servers
    for line in lines:
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        name = cells[0].strip("`")
        if name.lower() == "server":
            continue
        servers.append(
            {
                "name": name,
                "status": cells[1] if len(cells) > 1 else "",
                "transport": cells[2] if len(cells) > 2 else "",
                "source": cells[3] if len(cells) > 3 else "",
                "description": _scrub_legacy_runtime_text(cells[4] if len(cells) > 4 else ""),
                "registry": str(registry),
            }
        )
    return servers


def load_mcp_tools_for_status() -> list[dict[str, Any]]:
    return [
        {
            "name": f"mcp:{server['name']}",
            "description": server.get("description") or f"{server['name']} MCP server",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server": {"type": "string", "const": server["name"]},
                    "transport": {"type": "string"},
                },
            },
            "server": server,
        }
        for server in load_mcp_servers()
    ]


def load_mcp_resources_for_status() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for path in (
        shared_mcp_root() / "registry.md",
        shared_mcp_root() / "skill-integration.md",
        shared_mcp_root() / "config-templates" / "codex.toml",
        shared_mcp_root() / "config-templates" / "claude.mcp.json",
        agents_repo_root() / "agents" / "catalog.json",
    ):
        if not path.is_file():
            continue
        resources.append(
            {
                "name": path.name,
                "uri": str(path),
                "description": f"Shared agents repository resource: {path.relative_to(agents_repo_root())}",
                "mimeType": "application/json" if path.suffix == ".json" else "text/markdown",
            }
        )
    return resources


def resolve_agent_executor_url() -> str:
    return (
        os.getenv("ARCHIVIST_AGENT_EXECUTOR_URL")
        or os.getenv("ARCHIVIST_AGENT_CHAT_URL")
        or os.getenv("AGENT_EXECUTOR_URL")
        or ""
    ).strip().rstrip("/")


def resolve_agent_executor_token() -> str:
    return (
        os.getenv("ARCHIVIST_AGENT_EXECUTOR_TOKEN")
        or os.getenv("ARCHIVIST_AGENT_CHAT_TOKEN")
        or os.getenv("AGENT_EXECUTOR_TOKEN")
        or ""
    ).strip()


def resolve_agent_chat_model(agent_id: str | None = None) -> str:
    configured = (os.getenv("ARCHIVIST_AGENT_CHAT_MODEL") or "").strip()
    if configured:
        return configured
    aid = (agent_id or console_agent_id()).strip() or console_agent_id()
    return f"agents/{aid}"


def inspect_agent_runtime() -> dict[str, Any]:
    root = agents_repo_root()
    catalog_path = _agent_catalog_path()
    agents = load_team_agents()
    skills = load_shared_skills()
    mcp_servers = load_mcp_servers()
    executor_url = resolve_agent_executor_url()
    token = resolve_agent_executor_token()
    errors: list[str] = []
    executor_available = False
    version = None

    if not root.exists():
        errors.append("agents_repo_missing")
    if not catalog_path.is_file():
        errors.append("agent_catalog_missing")
    if not skills:
        errors.append("skills_catalog_empty")
    if not mcp_servers:
        errors.append("mcp_registry_empty")

    if executor_url:
        try:
            response = requests.get(f"{executor_url}/health", timeout=3)
            if response.ok:
                try:
                    payload = response.json()
                except Exception:
                    payload = {}
                executor_available = bool(payload.get("ok", True))
                version = payload.get("version")
            else:
                errors.append(f"executor_http_{response.status_code}")
        except Exception as exc:
            errors.append(f"executor_unreachable:{exc}")
        if not token:
            errors.append("executor_token_missing")

    ids = registered_agent_ids()
    registered = console_agent_id() in ids
    if not registered:
        errors.append("console_agent_not_in_catalog")

    catalog_available = root.exists() and catalog_path.is_file() and bool(agents)
    execution_configured = bool(executor_url and token)
    return {
        "available": catalog_available,
        "execution_available": executor_available and execution_configured,
        "backend": "agents-repository",
        "executor_url": executor_url or None,
        "binary": str(root),
        "version": version,
        "model": resolve_agent_chat_model(console_agent_id()),
        "workspace_path": host_workspace(),
        "workspace_mounted": Path(host_workspace()).exists(),
        "agents_root": str(root),
        "agents_count": len(agents),
        "skills_count": len(skills),
        "mcp_server_count": len(mcp_servers),
        "console_agent_id": console_agent_id(),
        "config_path": str(catalog_path) if catalog_path.is_file() else None,
        "token_configured": bool(token),
        "executor_configured": execution_configured,
        "registered": registered,
        "errors": errors,
    }


def load_agent_sessions_for_agents(agent_ids: list[str] | None = None) -> list[dict[str, Any]]:
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
                session_file = resolve_agent_session_file(meta.get("sessionFile"))
                message_count = 0
                last_message = ""
                title = str(session_key)
                if session_file and session_file.is_file():
                    messages = load_agent_messages_from_transcript(session_file)
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
                    "source": "agents",
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


def resolve_agent_session_file(path_text: str | None) -> Path | None:
    raw = str(path_text or "").strip()
    if not raw:
        return None
    candidates = [
        Path(raw),
        Path(raw.replace("/home/node/.claude/", str(Path.home() / ".claude") + "/")),
        Path(raw.replace("/home/andy/.claude/", str(Path.home() / ".claude") + "/")),
        agents_repo_root() / raw.lstrip("/"),
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return None


def load_agent_messages_from_transcript(session_file: Path) -> list[dict[str, Any]]:
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


def _agent_session_roots() -> list[Path]:
    explicit = (os.getenv("ARCHIVIST_AGENT_SESSIONS_ROOT") or "").strip()
    candidates = [
        Path(explicit).expanduser() if explicit else None,
        agents_repo_root() / "sessions",
        shared_agents_root(),
        Path.home() / ".claude" / "agents",
    ]
    out: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        if candidate not in out:
            out.append(candidate)
    return out


def _first_readable_session_store(agent_id: str) -> Path | None:
    for root in _agent_session_roots():
        for candidate in (
            root / agent_id / "sessions" / "sessions.json",
            root / agent_id / "sessions.json",
        ):
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
