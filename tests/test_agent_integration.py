from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_integration as ai


def test_host_workspace_points_to_repo_root():
    assert ai.host_workspace() == str(Path(__file__).resolve().parents[1])


def test_build_agent_system_message_contains_real_workspace():
    message = ai.build_agent_system_message("archivist-main")
    workspace = str(Path(__file__).resolve().parents[1])
    assert "archivist" in message.lower()
    assert workspace in message
    assert "/app" not in message.split("not /app", 1)[0].lower()


def test_build_agent_system_message_mentions_agent_docs():
    message = ai.build_agent_system_message("archivist-main")
    assert "openclaw-team/agents/archivist-main" in message
    assert "Agent identity (archivist-main)" in message


def test_load_team_agents_discovers_archivist_main():
    agents = ai.load_team_agents()
    agent_ids = {agent.get("agent_id") for agent in agents}
    assert "archivist-main" in agent_ids


def test_encode_decode_session_ref_round_trip():
    encoded = ai.encode_session_ref("archivist-main", "main:web:demo@archivist-main")
    assert encoded == "agent:archivist-main:main:web:demo@archivist-main"
    assert ai.decode_session_ref(encoded) == ("archivist-main", "main:web:demo@archivist-main")


def test_gateway_session_key_uses_agent_prefix():
    assert (
        ai.gateway_session_key("archivist-main", "main:web:demo@archivist-main")
        == "agent:archivist-main:main:web:demo@archivist-main"
    )


def test_example_openclaw_config_uses_repo_root_workspaces():
    example = (Path(__file__).resolve().parents[1] / "openclaw-team" / "openclaw.archivist-agents.example.json5").read_text(
        encoding="utf-8"
    )
    assert "/home/andy/archivist/openclaw-team/agents/" not in example
    assert example.count('workspace: "/home/andy/archivist"') >= 5


def test_openclaw_config_candidates_prefer_repo_local_override(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(tmp_path / "explicit.json"))
    monkeypatch.setenv("OPENCLAW_STATE_DIR", str(tmp_path / "state"))
    candidates = ai._openclaw_config_candidates()

    assert candidates[0] == tmp_path / "explicit.json"
    assert candidates[1] == tmp_path / "state" / "openclaw.json"
    assert candidates[2] == Path(__file__).resolve().parents[1] / ".openclaw" / "openclaw.json"


def test_load_openclaw_sessions_falls_back_to_main_store(tmp_path, monkeypatch):
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
        "main:web:test@archivist-main": {
            "updatedAt": 1775526795608,
            "sessionFile": str(session_file),
            "systemPromptReport": {"sessionKey": "main:web:test@archivist-main"},
        }
    }
    (main_sessions_dir / "sessions.json").write_text(json.dumps(store), encoding="utf-8")

    monkeypatch.setattr(ai, "_openclaw_agents_roots", lambda: [agents_root])

    sessions = ai.load_openclaw_sessions_for_agents(["archivist-main"])
    assert len(sessions) == 1
    assert sessions[0]["agentId"] == "archivist-main"
    assert sessions[0]["sessionKey"] == "main:web:test@archivist-main"
    assert sessions[0]["lastMessage"] == "/home/andy/archivist"


def test_load_openclaw_sessions_skips_unrouted_default_store_entries(tmp_path, monkeypatch):
    agents_root = tmp_path / "agents"
    default_sessions_dir = agents_root / "default" / "sessions"
    default_sessions_dir.mkdir(parents=True)
    (default_sessions_dir / "session-1.jsonl").write_text("", encoding="utf-8")
    (default_sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "agent:default:openai:test-session": {
                    "updatedAt": 1775526795608,
                    "sessionFile": str(default_sessions_dir / "session-1.jsonl"),
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ai, "_openclaw_agents_roots", lambda: [agents_root])

    assert ai.load_openclaw_sessions_for_agents(["archivist-main"]) == []


def test_load_openclaw_sessions_reads_all_candidate_stores(tmp_path, monkeypatch):
    agents_root = tmp_path / "agents"

    agent_sessions_dir = agents_root / "archivist-main" / "sessions"
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
                "main:web:restored@archivist-main": {
                    "updatedAt": 1775526795608,
                    "sessionFile": str(routed_session_file),
                    "systemPromptReport": {"sessionKey": "main:web:restored@archivist-main"},
                }
            }
        ),
        encoding="utf-8",
    )
    (default_sessions_dir / "session-noise.jsonl").write_text("", encoding="utf-8")
    (default_sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "agent:default:openai:noise": {
                    "updatedAt": 1775526795609,
                    "sessionFile": str(default_sessions_dir / "session-noise.jsonl"),
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ai, "_openclaw_agents_roots", lambda: [agents_root])

    sessions = ai.load_openclaw_sessions_for_agents(["archivist-main"])
    assert len(sessions) == 1
    assert sessions[0]["sessionKey"] == "main:web:restored@archivist-main"
    assert sessions[0]["storeOwner"] == "main"
