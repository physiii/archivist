# Archivist UI: Theme Update & Agent Console Integration Plan

## Overview

Port the Twin project's Material Design system (color palette, radius, typography) and Agent Console into Archivist. The archivist UI is pure CSS + React (no MUI), so we adapt the design tokens without adding MUI as a dependency.

## 1. Theme / Color Palette Update

**Current** → **Target** (match Twin's design tokens):

| Token | Archivist Now | Twin Target |
|-------|--------------|-------------|
| Primary accent | `#e39a22` (orange) | `#5b8cff` (blue) |
| Secondary | — | `#2dd4bf` (teal) |
| Selection bg | `rgba(227,154,34,0.28)` | `rgba(91,140,255,0.28)` |
| Active nav bg | `rgba(227,154,34,0.1)` | `rgba(91,140,255,0.10)` |
| Active nav icon | `#e39a22` | `#5b8cff` |
| Brand gradient | `#e39a22, #c17f10` | `#5b8cff, #2dd4bf` |
| Chat fab bg | `#e39a22` | `linear-gradient(135deg, #5b8cff 0%, #3d6be0 100%)` |
| Chat fab shadow | — | `0 4px 20px rgba(91,140,255,0.35)` |
| Tabs active | `#e39a22` border/bg | `#5b8cff` |
| Segmented active | `rgba(227,154,34,0.12)` | `rgba(91,140,255,0.12)` |
| Snapshot active | `#e39a22` border | `#5b8cff` border |
| Button hover border | `#e39a22` | `#5b8cff` |
| Border default | `rgba(255,255,255,0.06)` | `rgba(255,255,255,0.07)` |
| Card radius | `10px` | `10px` ✓ (keep) |
| Panel radius | `10px` | `10px` ✓ (keep) |
| Scrollbar thumb | `rgba(255,255,255,0.1)` | `rgba(255,255,255,0.08)` |
| Scrollbar width | `6px` | `5px` |
| OC kind badge | `#e39a22` | `#5b8cff` |

**Files to change:** `ui/src/index.css`

## 2. Add CSS Variables

Add proper CSS custom properties to `:root` for theming consistency:

```css
:root {
  --primary: #5b8cff;
  --primary-dark: #3d6be0;
  --secondary: #2dd4bf;
  --bg-dark: #0a0e14;
  --bg-surface-0: #0d1117;
  --bg-surface-1: #111820;
  --border: rgba(255,255,255,0.07);
  --text-primary: rgba(255,255,255,0.92);
  --text-secondary: rgba(180,195,210,0.68);
}
```

## 3. Agent Console Page

Create `ui/src/pages/ConsolePage.tsx` — a simplified version of Twin's `AgentConsole.tsx` adapted for Archivist (pure CSS, no MUI).

**Features (Chat tab only — Fleet/System/Tests not applicable to Archivist):**
- SSE streaming chat with the configured agent executor
- Session list (local + shared agent sessions)
- Quick action chips
- Message bubbles (user, assistant, system, tool)
- Markdown rendering for assistant messages
- New session / stop controls
- Streaming indicator

**Key differences from Twin:**
- No MUI — use CSS classes matching archivist's style
- Reuse existing `/api/chat` endpoint with agent executor SSE streaming
- Reuse existing `/api/chat/sessions` endpoint
- Add a simple markdown renderer (or use `react-markdown` if we add it)

## 4. Sidebar Integration

Add "Console" nav item at the **bottom** of sidebar nav, with a divider separating it from the main nav items:

```
Collections    (search & browse)
Backup         (schedules & logs)
Indexing       (pipelines & status)
Media          (processing pipeline)
─────────────────────────────────
Console        (agent chat)          ← new
```

**Route:** `/console`

**Files to change:** `ui/src/App.tsx`

## 5. Dependencies

Add `react-markdown` and `remark-gfm` for markdown rendering in the console:
```
npm install react-markdown remark-gfm
```

## 6. Implementation Status — COMPLETE

All steps implemented and build verified:

1. [x] **Updated `index.css`** — swapped all orange (#e39a22) to blue (#5b8cff), added CSS variables, added console + markdown styles, updated borders to 0.07
2. [x] **Added react-markdown + remark-gfm** dependencies
3. [x] **Created `components/MarkdownMessage.tsx`** — pure CSS markdown renderer
4. [x] **Created `pages/ConsolePage.tsx`** — full agent console with SSE streaming, sessions, quick actions
5. [x] **Updated `App.tsx`** — added Console nav item with divider + /console route
6. [x] **Updated `pages/MediaPage.tsx`** — replaced remaining orange refs
7. [x] **Build passes** — `npm run build` clean, no TypeScript errors
