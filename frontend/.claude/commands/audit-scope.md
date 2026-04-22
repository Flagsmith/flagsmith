---
description: Audit a directory or glob pattern against the Flagsmith design system.
argument-hint: <path-glob> (e.g., "frontend/web/components/**/*.scss")
---

Use the `design-auditor` subagent to audit everything matching `$ARGUMENTS`.

Pass these explicit instructions to the auditor:

1. The scope is `$ARGUMENTS`. Limit `Glob` and `Grep` patterns to match this scope.
2. If the scope contains more than 200 files, sample a representative cross-section rather than exhaustively scanning. State the sampling ratio explicitly in the report.
3. Group findings by **file** as well as by severity, so the user sees which components are in worst shape.
4. At the end of the report, add a "Hotspots" section listing the 5 files with the most findings.
5. Report in British English (colour, organise, centre).

When the auditor returns its report, present it to the user verbatim.

## Runtime verification (required when fixes are applied)

If the user asks you to apply any of the findings, you MUST verify the result in a live browser via Chrome DevTools MCP before reporting the task complete. Static analysis misses shared-component render output, dynamic-colour contrast, dark-mode flips, focus rings, responsive behaviour, and regressions introduced by your own edits.

Procedure:

1. Apply the static fixes.
2. For each affected route (or a representative sample if scope spans many), open it via `mcp__chrome-devtools__navigate_page` and use `take_snapshot` + `take_screenshot`.
3. **Element-aware typography check (mandatory).** Use `mcp__chrome-devtools__evaluate_script` to extract computed `fontFamily`, `fontSize`, `fontWeight`, `lineHeight` for every heading, descriptor, button label, input, table cell, and card title in the changed files. Check each against its expected role per `typography.md` + `composition.md` §6 (h1/h2 page title 34/40 600, h4 section 24/32 600, h5 card 18/28 600, descriptor 13/18 400 in `--color-text-secondary`, body 14/20 400, overline 11/16 500 UPPERCASE). Off-scale sizes (15/17/19/21/22 px) are automatic findings. Heading tags used purely for visual weight are findings.
4. **Element-aware spacing check (mandatory).** Measure computed `padding` / `margin` / `gap` against the Bootstrap scale (0/4/8/16/24/32 px) and the composition gaps (heading→descriptor 4–6 px, descriptor→content 12–16 px, card padding 16/24 px, field stack 16 px, section gap 24/32 px). Any off-scale value is a finding — report actual pixel and selector.
5. Check both light and dark mode, and at least 375 px + 1440 px widths if layout/spacing/composition was touched. Verify touch targets clear 44×44 at 375 px via `getBoundingClientRect`.
6. Confirm the fixes rendered and no regressions appeared. Fix any regression in the same turn.

Do not offer a runtime pass as a follow-up question — just run it.

For deeper coverage delegate to the `runtime-auditor` subagent (`frontend/.claude/agents/runtime-auditor.md`) — the typography and spacing checks above are the non-negotiable minimum.
