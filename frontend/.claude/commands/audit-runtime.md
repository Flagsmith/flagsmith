---
description: Audit a live page via Chrome DevTools MCP against the Flagsmith design system.
argument-hint: <url-or-path> [states=default,hover,focus] [viewports=desktop,tablet]
---

Use the `runtime-auditor` subagent to audit the live page at `$ARGUMENTS`.

Pass these explicit instructions:

1. Target URL: parse from `$ARGUMENTS`. If no URL is given, ask once. Default to `http://localhost:8080` (Flagsmith frontend dev server — `ENV=local npm run dev` in `frontend/`).
2. States to cover: extract from `$ARGUMENTS` (look for `states=...`). Default to `default,hover,focus` if unspecified.
3. Viewports to cover: extract from `$ARGUMENTS` (look for `viewports=...`). Default to `desktop` (1440×900) only.
4. Run the full six-phase audit: environment check → token drift check → page sweep → component audit → interactive state audit → accessibility live checks → viewport sweep.
5. Flagsmith is dual-mode — audit both light and dark where both are reachable. Dark mode is applied by `web/project/darkMode.ts`: `.dark` goes on `<body>`, `data-bs-theme="dark"` on `<html>`, and state persists in `localStorage.dark_mode`. Toggle via `evaluate_script` with the canonical snippet in `frontend/.claude/agents/runtime-auditor.md` (class on body + data-bs-theme on html + localStorage + reload for components that read `getDarkMode()` at mount). A value that passes light but fails dark (or vice versa) is a finding.
6. Screenshot every critical finding.
7. Clean up overlays and tabs at the end.
8. Report in British English (colour, organise, centre).

When the auditor returns, present the report verbatim.

## Pre-flight

Before delegating, verify Chrome DevTools MCP is connected by checking whether `list_pages` tools are available. If not, tell the user:

> Chrome DevTools MCP isn't connected. Install with `claude plugin install chrome-devtools-mcp` (or check https://claude.com/plugins/chrome-devtools-mcp), then restart Claude Code. Once connected, re-run this command.

and stop.

## Safety check

If `$ARGUMENTS` contains a production URL (anything not `localhost`, `127.0.0.1`, or a known staging domain), confirm with the user before delegating:

> You're about to audit a live production URL. The auditor is read-only and won't modify the page, but it will drive your browser — clicking elements, hovering, focusing. OK to proceed? (yes / cancel)

Wait for explicit yes.
