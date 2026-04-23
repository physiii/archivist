# Agent Workspace Rules — Archivist Verifier

- Validate Archivist changes with tests, builds, and live smoke checks
- Use `/home/andy/archivist` as the project root
- Block completion when verification is missing
- Treat `focus-priorities` as a required profile for changes touching `/api/focus/*`, `/api/tests/*`, `ui/src/pages/FocusPage.tsx`, or `ui/src/console/*`
- Fail the review if focus-priority performance tests regress or the latest report is stale
