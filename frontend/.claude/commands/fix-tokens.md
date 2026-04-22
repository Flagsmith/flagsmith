---
description: Audit a path, then apply mechanical token fixes. Runs design-auditor followed by token-fixer.
argument-hint: <path-to-file-or-directory>
---

This command runs a two-phase workflow against `$ARGUMENTS`:

## Phase 1 — Audit

Delegate to the `design-auditor` subagent with scope `$ARGUMENTS`. Request that it:

1. Run the full audit.
2. **Flag each finding with a `mechanical-fix-safe` attribute** (`true` / `false`). Safe fixes are those in the token-fixer substitution set: hex-to-colour-token, primitive-scss-to-CSS-var, px-to-radius-token (only for exact scale matches), raw duration/alpha tokenisation.
3. Return the report to the main agent.
4. Report in British English (colour, organise, centre).

Show the audit report to the user.

## Phase 2 — Ask for confirmation

Present this summary to the user:

> The auditor found **N** total findings. **M** are safe mechanical fixes I can apply automatically (no visual change). **(N−M)** need designer input or main-agent work and I will leave them alone.
>
> Apply the **M** mechanical fixes now? (yes / no / review-first)

Wait for an explicit yes before proceeding.

## Phase 3 — Fix (only if confirmed)

Delegate to the `token-fixer` subagent. Pass it:

- The audit report from phase 1.
- Explicit instruction to apply **only** findings marked `mechanical-fix-safe: true`.
- Scope `$ARGUMENTS`.

When the fixer returns its report, present it to the user verbatim.

## Phase 4 — Verify (static)

Re-run the `design-auditor` on the same scope. The new finding count should be lower by approximately M (the number of fixes applied). Any delta beyond that deserves investigation — report it clearly.

## Phase 5 — Verify (runtime, required)

After phase 4, open the affected route(s) in a live browser via Chrome DevTools MCP. This is not optional — static analysis misses shared-component render output, dynamic-colour contrast, dark-mode flips of token substitutions, focus-ring behaviour, responsive layout, and regressions introduced by the fixer.

Procedure:

1. Use `mcp__chrome-devtools__navigate_page` (or `new_page`) to open the route that renders the fixed files. If the fix touched a shared component, open at least one route per consumer.
2. `take_snapshot` + `take_screenshot`.
3. **Element-aware typography check (mandatory).** Use `mcp__chrome-devtools__evaluate_script` to extract computed `fontFamily`/`fontSize`/`fontWeight`/`lineHeight` for every heading, descriptor, button, input, table cell, and card title in the fixed files. Check each against `typography.md` + `composition.md` §6. Off-scale sizes (15/17/19/21/22 px) are automatic findings. A substitution like `#9DA4AE` → `var(--color-icon-secondary)` shouldn't change typography, so any computed-typography delta after the fix is a regression worth investigating.
4. **Element-aware spacing check (mandatory).** Measure computed `padding`/`margin`/`gap` on the elements affected by the fix and their parents, against the Bootstrap scale (0/4/8/16/24/32 px) and the composition gaps (heading→descriptor 4–6 px, descriptor→content 12–16 px, card padding 16/24 px, field stack 16 px, section gap 24/32 px). Any off-scale value is a finding — report actual pixel and selector. Pay particular attention when a fix replaces a heading tag with a non-heading tag: the tag default may have been providing line-height / margin the spacing now lacks.
5. Toggle dark mode via `evaluate_script` and re-read computed values. Dark mode is applied by `web/project/darkMode.ts`: `.dark` goes on `<body>` (not `<html>`), `data-bs-theme="dark"` on `<html>`, and state persists in `localStorage.dark_mode`. Use the canonical snippet in `frontend/.claude/agents/runtime-auditor.md` — set localStorage + both element attributes + reload if any affected component reads `getDarkMode()` at mount. Confirm dark-mode flip. Mode-specific regressions are separate findings. Restore original state before leaving.
6. If layout/spacing/composition was fixed, `resize_page` to 375 px and 1440 px and re-check.
7. Report any visual regression clearly. Do not mark the task complete without this step.

Do not offer the runtime pass as a follow-up question — run it as part of the workflow.

For deeper coverage (full page sweep, tertiary states, cross-page consistency) delegate to the `runtime-auditor` subagent defined in `frontend/.claude/agents/runtime-auditor.md`. The typography and spacing checks above are the non-negotiable minimum.

## Safety rules for the main agent

- Never let the fixer run without an explicit yes from the user.
- Never run the fixer on paths matching `node_modules/`, `dist/`, `build/`, `.next/`, generated folders, or the design-system definition files themselves (`frontend/web/styles/_tokens.scss`, `frontend/web/styles/_primitives.scss`, `frontend/web/styles/_variables.scss`, `frontend/common/theme/tokens.json`).
- If the audit report contains zero `mechanical-fix-safe: true` findings, skip phase 2–4 and tell the user there's nothing the fixer can safely do.
