# Archivist Agent Team Rules

Each Archivist agent is registered against the full repo workspace at `/home/andy/archivist`.
Agent-specific identity and memory docs live under `openclaw-team/agents/<agent-id>/`.

## Agents

| ID | Role | Emoji |
|----|------|-------|
| archivist-main | Human-facing operator for the Archivist app | A |
| archivist-health | Runtime and service health monitor | H |
| archivist-repair | Focused implementation worker | R |
| archivist-observer | Post-session forensic analyst | O |
| archivist-verifier | Validation and regression gate | V |

## Routing

- Console and web chat go to `archivist-main`
- Health/system review routes go to `archivist-health`
- Repair work routes go to `archivist-repair`
- Investigation routes go to `archivist-observer`
- Verification routes go to `archivist-verifier`

## Rules

- Every agent should know the real project root is `/home/andy/archivist`
- Agent bootstrap docs live under `/home/andy/archivist/openclaw-team/agents/<agent-id>`
- OpenClaw `workspace` entries should point to `/home/andy/archivist`, not the metadata subdirectory
- Shared skills live under `/media/mass/agents/skills`
- Prefer explicit agent ids over `openclaw/default`
