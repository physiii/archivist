# Agent Workspace Rules — Archivist Main

This workspace belongs to `archivist-main`.

## Session startup

1. Read `IDENTITY.md`
2. Read `SOUL.md`
3. Read `agent-manifest.json`
4. Check recent memory if present

## Role discipline

- Own the console, chat, and direct operator interactions
- Use `/home/andy/archivist` as the real project root
- Treat `openclaw-team/agents/archivist-main` as the bootstrap-docs directory, not the whole app

## Project structure

- `main.py` — Flask routes and app wiring
- `backups_service.py` — backup orchestration
- `indexing_service.py` — indexing orchestration
- `media/` — media pipeline and evidence store
- `ui/src/` — React interface
- `tests/` — pytest and Playwright coverage

## Verification

- `pytest`
- `cd ui && npm run build`
- Rebuild and restart the Archivist container when deployment changes are required
