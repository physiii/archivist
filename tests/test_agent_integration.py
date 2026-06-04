from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_integration as ai


def test_host_workspace_points_to_repo_root():
    assert ai.host_workspace() == str(Path(__file__).resolve().parents[1])


def test_build_agent_system_message_contains_real_workspace():
    message = ai.build_agent_system_message("operator-chat")
    workspace = str(Path(__file__).resolve().parents[1])
    assert "archivist" in message.lower()
    assert workspace in message
    assert "/app" not in message.split("not /app", 1)[0].lower()


def test_build_agent_system_message_mentions_shared_agents_repo():
    message = ai.build_agent_system_message("operator-chat")
    assert "/media/mass/agents" in message
    assert "Agent identity (operator-chat)" in message


def test_load_team_agents_discovers_shared_operator_chat():
    agents = ai.load_team_agents()
    agent_ids = {agent.get("agent_id") for agent in agents}
    assert "operator-chat" in agent_ids
    assert "runtime-health-monitor" in agent_ids


def test_load_shared_skills_discovers_catalog():
    skills = ai.load_shared_skills()
    skill_ids = {skill.get("id") for skill in skills}
    assert "engineering-code" in skill_ids
    assert "verification-gate" in skill_ids


def test_load_mcp_servers_discovers_registry():
    servers = ai.load_mcp_servers()
    server_names = {server.get("name") for server in servers}
    assert "llm-tools" in server_names


def test_encode_decode_session_ref_round_trip():
    encoded = ai.encode_session_ref("operator-chat", "main:web:demo@operator-chat")
    assert encoded == "agent:operator-chat:main:web:demo@operator-chat"
    assert ai.decode_session_ref(encoded) == ("operator-chat", "main:web:demo@operator-chat")


def test_agent_session_key_uses_agent_prefix():
    assert (
        ai.agent_session_key("operator-chat", "main:web:demo@operator-chat")
        == "agent:operator-chat:main:web:demo@operator-chat"
    )


def test_agent_session_roots_can_be_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCHIVIST_AGENT_SESSIONS_ROOT", str(tmp_path / "sessions"))
    roots = ai._agent_session_roots()

    assert roots[0] == tmp_path / "sessions"


def test_load_agent_sessions_falls_back_to_main_store(tmp_path, monkeypatch):
    agents_root = tmp_path / "agents"
    main_sessions_dir = agents_root / "main" / "sessions"
    main_sessions_dir.mkdir(parents=True)

    session_file = main_sessions_dir / "session-1.jsonl"
    session_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": "What is the workspace?"}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "/home/andy/archivist"}],
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    store = {
        "main:web:test@operator-chat": {
            "updatedAt": 1775526795608,
            "sessionFile": str(session_file),
            "systemPromptReport": {"sessionKey": "main:web:test@operator-chat"},
        }
    }
    (main_sessions_dir / "sessions.json").write_text(json.dumps(store), encoding="utf-8")

    monkeypatch.setattr(ai, "_agent_session_roots", lambda: [agents_root])

    sessions = ai.load_agent_sessions_for_agents(["operator-chat"])
    assert len(sessions) == 1
    assert sessions[0]["agentId"] == "operator-chat"
    assert sessions[0]["sessionKey"] == "main:web:test@operator-chat"
    assert sessions[0]["lastMessage"] == "/home/andy/archivist"


def test_load_agent_sessions_skips_unrouted_default_store_entries(tmp_path, monkeypatch):
    agents_root = tmp_path / "agents"
    default_sessions_dir = agents_root / "default" / "sessions"
    default_sessions_dir.mkdir(parents=True)
    (default_sessions_dir / "session-1.jsonl").write_text("", encoding="utf-8")
    (default_sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "agent:default:api:test-session": {
                    "updatedAt": 1775526795608,
                    "sessionFile": str(default_sessions_dir / "session-1.jsonl"),
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ai, "_agent_session_roots", lambda: [agents_root])

    assert ai.load_agent_sessions_for_agents(["operator-chat"]) == []


def test_load_agent_sessions_reads_all_candidate_stores(tmp_path, monkeypatch):
    agents_root = tmp_path / "agents"

    agent_sessions_dir = agents_root / "operator-chat" / "sessions"
    main_sessions_dir = agents_root / "main" / "sessions"
    default_sessions_dir = agents_root / "default" / "sessions"
    agent_sessions_dir.mkdir(parents=True)
    main_sessions_dir.mkdir(parents=True)
    default_sessions_dir.mkdir(parents=True)

    routed_session_file = main_sessions_dir / "session-routed.jsonl"
    routed_session_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": "Which workspace are you using?"}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "/home/andy/archivist"}],
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    (agent_sessions_dir / "sessions.json").write_text("{}", encoding="utf-8")
    (main_sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "main:web:restored@operator-chat": {
                    "updatedAt": 1775526795608,
                    "sessionFile": str(routed_session_file),
                    "systemPromptReport": {"sessionKey": "main:web:restored@operator-chat"},
                }
            }
        ),
        encoding="utf-8",
    )
    (default_sessions_dir / "session-noise.jsonl").write_text("", encoding="utf-8")
    (default_sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "agent:default:api:noise": {
                    "updatedAt": 1775526795609,
                    "sessionFile": str(default_sessions_dir / "session-noise.jsonl"),
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ai, "_agent_session_roots", lambda: [agents_root])

    sessions = ai.load_agent_sessions_for_agents(["operator-chat"])
    assert len(sessions) == 1
    assert sessions[0]["sessionKey"] == "main:web:restored@operator-chat"
    assert sessions[0]["storeOwner"] == "main"
