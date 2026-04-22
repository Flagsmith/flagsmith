---
description: Walk every route of a running app and audit each page via Chrome DevTools MCP. For full-app compliance sweeps.
argument-hint: <base-url> [routes=file-path-or-glob] [states=default,hover,focus]
---

Full-app compliance sweep. This is the "audit every page and every tab" workflow.

## Instructions to the main agent

1. Parse `$ARGUMENTS` for the base URL. If missing, default to `http://localhost:8080` (Flagsmith frontend dev server — `ENV=local npm run dev` in `frontend/`). Confirm with the user before proceeding.

2. Determine the route list:
   - If `routes=<path>` was provided, read that file (it should be a plain list of paths, one per line, or a JSON array).
   - Else, walk the primary Flagsmith routes: `/projects`, `/organisations/<id>/projects`, a feature-flags page, a segments page, an environment settings page. Ask the user for a concrete org/project/env id if needed to construct the URLs.
   - If neither source yields a list, ask the user.

3. Confirm the scope with the user before starting:

   > I'm about to audit **N routes** on `<base-url>` in states `<states>`. This will take approximately **N × 30 seconds** (~X minutes total). Proceed? (yes / narrow scope / cancel)

4. Wait for explicit yes.

## Delegate per-route

For each route, delegate to the `runtime-auditor` subagent with:

- Target URL: `<base-url><route>`
- States: inherited from `$ARGUMENTS` (default `default,hover,focus`)
- Viewports: desktop only unless otherwise specified (multi-viewport × multi-route would be too expensive for a full sweep — run those separately if needed)
- Phase 0 token drift check: **only on the first route** — once validated, skip on subsequent routes (tokens don't change per-page).
- Dual-mode: run the first route in both light and dark; subsequent routes inherit the mode behaviour unless a finding suggests mode-specific regressions.

Collect each per-route report. Don't pass them back to the user individually — **aggregate**.

## Aggregation

After all routes are audited, produce a single consolidated report (British English):

```
# Flagsmith full-app runtime audit

## Environment
<summary from phase 0, once>

## Coverage
- Routes audited: <N of M>
- Routes skipped (and why): <list>
- Total elements inspected: <N>
- Total findings: <N>

## Findings by route
### /projects — <N findings: X critical, Y major, Z minor>
<top 3 findings inline, link to per-route detail below>

### /organisations/<id>/projects — <N findings>
...

## Cross-route patterns
<The highest-value section. Look at every finding and identify:
 - Findings that appear on 3+ routes → this is a component-level bug, not a page bug.
   List which component, link to static-auditor suggestion.
 - Findings unique to one route → genuine page-level bugs.
 - Routes with zero findings → compliant pages, useful as reference implementations.>

## Global token health
<If phase 0 found any token drift, it's here. Otherwise "No token drift detected — primitives match the rule definitions.">

## Accessibility summary
<Aggregate a11y findings across all routes:
 - Focus ring violations: <N elements across <N routes>>
 - Target size violations: <N elements>
 - Contrast failures: <N>
 - Missing labels: <N>>

## Recommended fix order
1. **Primitive/token issues** (affect everything) — [if any]
2. **Shared-component issues** (affect many pages) — [list components, route to static auditor]
3. **Page-specific issues** (isolated) — [list per page]
4. **A11y must-fixes** — [prioritise target size and focus ring]

## Per-route detail
<collapsible sections or "see appendix"-style with full finding lists per route>
```

## Efficiency rules

- **Token drift check runs once.** Route 2+ inherit the result.
- **Parallel if possible.** If the runtime-auditor subagent and Chrome MCP support parallel tab sessions, audit routes in batches of 3–5. If not, sequential — but reuse the page object where possible (`navigate_page` is cheaper than `new_page`).
- **Short-circuit on fatal drift.** If phase 0 on the first route shows primitive tokens don't match the rules, **stop the sweep** and tell the user — auditing N pages against wrong primitives is wasted effort.
- **Budget check.** If the user requested >50 routes, warn that this will be long and expensive, and recommend narrowing to a representative subset (e.g., one per route template family) unless they explicitly confirm.

## Post-sweep cleanup

- Close all tabs the auditor opened.
- Reset the original tab to the state it was in before (if possible).
- Report any live pages that had JavaScript console errors during the audit — those are bugs worth flagging separately from styling.

## Pre-flight

As in `/audit-runtime`: verify Chrome DevTools MCP is connected before starting. If not, tell the user how to install and stop.
