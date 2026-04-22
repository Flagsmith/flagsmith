---
description: Audit a single component or file against the Flagsmith design system.
argument-hint: <path-to-file-or-component>
---

Use the `design-auditor` subagent to audit the file or directory at `$ARGUMENTS` against the Flagsmith design system rules.

Pass these explicit instructions to the auditor:

1. Scope is limited to `$ARGUMENTS`. Do not wander outside it.
2. Load all fourteen rule modules before starting (see `frontend/.claude/rules/`).
3. Run both mechanical (grep-able) and semantic checks.
4. Report findings grouped by severity.
5. Include the confidence calibration at the end.
6. Report in British English (colour, organise, centre).

When the auditor returns its report, present it to the user verbatim. Do not summarise or editorialise — the report is the deliverable.

## Runtime verification (required when fixes are applied)

If the user asks you to apply any of the findings from the audit, you MUST verify the result in a live browser via Chrome DevTools MCP before reporting the task complete. Static analysis misses: shared-component render output (e.g. what tag `PanelSearch` emits for its `title` prop), dynamic-colour contrast, dark-mode flip of token substitutions, focus-ring correctness on composed `<Link>`/`<Button>` pairs, responsive behaviour at 375/768, loader flash timing, and regressions you introduced (e.g. replacing `<h2>` with `<span>` that dropped inherited font-size).

Procedure:

1. Apply the static fixes.
2. Use `mcp__chrome-devtools__navigate_page` (or `new_page`) to open the route that renders the component. Use `take_snapshot` and `take_screenshot`.
3. **Element-aware typography check (mandatory).** For every heading, descriptor, button label, input, table cell, and card title in the changed component, use `mcp__chrome-devtools__evaluate_script` to extract computed `fontFamily`, `fontSize`, `fontWeight`, and `lineHeight`, then check against the expected role per `typography.md` and `composition.md` §6:
   - `<h1>`/`<h2>` page title → 34/40 weight 600 (`$h2-font-size`).
   - `<h2>` section / `<h4>` group heading → 24/32 weight 600.
   - `<h5>` card title → 18/28 weight 600.
   - `<p>` descriptor following a heading → 13/18 (`$font-caption`) weight 400, colour `var(--color-text-secondary)`.
   - Body `<p>` / table cell / menu item → 14/20 weight 400.
   - Button default → 14/20 weight 500/600 depending on variant.
   - Overline / badge / tiny label → 11/16 weight 500 UPPERCASE (`$font-caption-xs`).
   Off-scale sizes (15, 17, 19, 21, 22 px) are an automatic finding even if the component "looks right."
   Also verify a heading tag hasn't been used purely for visual weight (a single-letter `<h2>` avatar, a `<h5>` used because it's "medium-bold") — mismatch against §6 is a finding.
4. **Element-aware spacing check (mandatory).** Measure the gaps that `spacing.md` and `composition.md` pin down, via `getBoundingClientRect` or computed `padding`/`margin`/`gap` on the relevant parents:
   - Heading → descriptor gap: 4–6 px.
   - Descriptor → content gap: 12–16 px.
   - Card padding: 16 or 24 px.
   - Form-field stack gap: 16 px (`gap-3`).
   - Section → section gap: 24 px (`mb-4`) or 32 px (`mb-5`) in comfortable density.
   - Dashboard / card-grid gap: 16 px (`gap-3`).
   Values off the Bootstrap scale (0, 4, 8, 16, 24, 32 px) are a finding. 13 px, 15 px, 18 px, 20 px, 30 px, 40 px — all flag. Report the actual pixel and the parent selector.
5. Check both light and dark mode. Dark mode is applied by `web/project/darkMode.ts`: `.dark` goes on `<body>` (not `<html>`), `data-bs-theme="dark"` on `<html>`, and state persists in `localStorage.dark_mode`. Use the canonical toggle snippet (see `frontend/.claude/agents/runtime-auditor.md`): set localStorage, set `<body class="dark">`, set `<html data-bs-theme="dark">`, and reload if the component reads `getDarkMode()` at mount. Mode-specific regressions go in their own finding. Restore original state before leaving.
6. Resize to at least 375 px and 1440 px via `mcp__chrome-devtools__resize_page` if the fixes touched layout, spacing, or composition. At 375 px, verify touch-target sizes clear 44×44 via `getBoundingClientRect` on every interactive element inside the changed component.
7. Confirm the fixes rendered and no regressions were introduced. If a regression is visible, fix it in the same turn.

Do not offer a runtime pass as a follow-up question — just run it. The user has already asked for it by invoking the audit + fix workflow.

For deeper coverage (full page sweep, tertiary states, cross-page consistency), delegate to the `runtime-auditor` subagent — it runs the full six-phase audit defined in `frontend/.claude/agents/runtime-auditor.md`. The element-aware typography and spacing checks above are the non-negotiable minimum.
