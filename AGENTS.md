# Archivist Workspace Rules

## Workspace

- Primary workspace: `/home/andy/archivist`
- Agent identity docs: `openclaw-team/agents/<agent-id>/`
- UI: `ui/src/`
- API: `main.py`
- Media pipeline: `media/`
- Tests: `tests/` and `ui/tests/`

## Startup

1. Treat `/home/andy/archivist` as the authoritative workspace root.
2. Read `IDENTITY.md`, `SOUL.md`, and the matching files under `openclaw-team/agents/<agent-id>/`.
3. Use repo-relative evidence when discussing behavior or proposing fixes.

## Working rules

- Keep chat, fleet, system, and settings flows aligned with the actual OpenClaw runtime.
- Prefer repo-root OpenClaw workspaces so agents can inspect and modify the real codebase.
- Verify container and gateway behavior after changes; unit tests alone are not enough.
