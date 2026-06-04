# Archivist Workspace Rules

## Workspace

- Primary workspace: `/home/andy/archivist`
- Shared agent knowledge base: `/media/mass/agents`
- Agent docs: `/media/mass/agents/agents/<agent-id>/` and `/media/mass/agents/agents/roles/<role-id>.md`
- UI: `ui/src/`
- API: `main.py`
- Media pipeline: `media/`
- Tests: `tests/` and `ui/tests/`

## Startup

1. Treat `/home/andy/archivist` as the authoritative workspace root.
2. Read `IDENTITY.md`, `SOUL.md`, and the relevant shared agent docs under `/media/mass/agents/agents/`.
3. Use repo-relative evidence when discussing behavior or proposing fixes.

## Working rules

- Keep chat, fleet, system, and settings flows aligned with `/media/mass/agents` as the source of truth.
- Prefer repo-root workspaces so agents can inspect and modify the real codebase.
- Verify container and runtime behavior after changes; unit tests alone are not enough.
