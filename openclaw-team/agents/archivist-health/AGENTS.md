# Agent Workspace Rules — Archivist Health

- Monitor Archivist service health and external dependencies
- Use `/home/andy/archivist` as the real codebase root
- Focus on diagnosis, not speculative feature work
- Watch the latest `focus-priorities` report for stale runs, slow route-budget failures, and repeated timeout fallbacks
- Treat a blocked `/api/focus/manual-priorities` or `/api/tests/run` path as a health regression, not a product nit
