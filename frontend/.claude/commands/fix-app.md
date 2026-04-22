---
description: Closed-loop design system fix. Runtime audit → static audit → mechanical fixes → runtime re-verify. The "apply the system retroactively" workflow.
argument-hint: <base-url> [routes=<file>] [auto-fix=true|false]
---

This is the end-to-end "retrofit the design system onto an existing app" workflow. It chains four subagents across four phases.

## The four phases

```
  PHASE 1               PHASE 2               PHASE 3               PHASE 4
  Runtime audit         Static audit          Mechanical fixes      Runtime verify
  ────────────          ────────────          ────────────          ────────────
  runtime-auditor       design-auditor        token-fixer           runtime-auditor
  (live DOM)            (source code)         (source code)         (live DOM)
       ↓                     ↓                     ↓                     ↓
   "these elements       "these source         "applied N safe      "N findings
    render wrong"         files violate"        fixes"                remain"
```

The insight: runtime findings tell you **what's wrong on screen**; the static auditor tells you **where in the source**; the fixer applies the mechanical ones; the re-runtime confirms the fix landed in the rendered output, not just in the file.

## Instructions to the main agent

Report in British English throughout (colour, organise, centre).

### Phase 0 — Pre-flight

1. Parse `$ARGUMENTS`: base URL (default `http://localhost:8080` — Flagsmith frontend dev server, `ENV=local npm run dev` in `frontend/`), optional routes file, optional `auto-fix=true|false` (default `false` — fixes require confirmation).
2. Verify Chrome DevTools MCP is connected. If not, stop and instruct.
3. Confirm scope with the user:

   > I'm about to run the full closed-loop workflow:
   > - Runtime audit of **N routes** on `<base-url>`
   > - Static audit of the source code files implicated by runtime findings
   > - Mechanical fixes (with confirmation unless `auto-fix=true`)
   > - Runtime re-audit to verify the fixes landed
   >
   > Estimated time: **X minutes**. Proceed? (yes / cancel)

4. Wait for explicit yes.

### Phase 1 — Runtime audit

Delegate to `runtime-auditor`. Scope, states, viewports as specified. Request the **aggregated cross-route report format** so findings are already grouped by "shared-component" vs "page-specific". Flagsmith is dual-mode — request both light and dark coverage on the first route so mode-specific regressions surface.

When the report comes back:

- Store it (in conversation context, or if large, write to `frontend/.claude/audit-reports/runtime-<timestamp>.md` and reference by path).
- Extract findings that the auditor flagged as "route to static auditor — likely shared-component fix". These are the high-leverage issues — one source fix, many pages fixed.

### Phase 2 — Static audit (targeted)

For each runtime finding that implicates a source file, delegate to `design-auditor` with narrow scope:

- Scope: the specific component directory the runtime auditor named (e.g., `frontend/web/components/base/forms/**`, `frontend/web/components/modals/**`).
- Request: "Verify the runtime finding `<quoted>` has a source-level cause in this scope, and report all related violations."

The static auditor may find additional violations in the same files that the runtime auditor couldn't see (e.g., hardcoded hex values that aren't yet rendered because they're on a state the user didn't hit).

### Phase 3 — Consolidate and confirm

Merge the runtime and static reports. Present to the user:

```
# Closed-loop audit — Phase 3 summary

## Runtime findings (what's broken on screen)
- Critical: N
- Major: N
- Minor: N

## Source-level root causes
- Shared-component issues affecting multiple pages: <N components, listed>
- Page-specific issues: <N pages>
- Primitive/token drift: <present | absent>

## Mechanically fixable now
- **N** findings are safe mechanical substitutions (hex→CSS var, primitive-scss→CSS var, px→radius-token, raw duration/alpha tokenisation).
- **M** findings require designer input or non-mechanical code changes.

## Proposed fix plan
1. <list of files that will be touched, summarised>

Apply the **N** mechanical fixes now? (yes / review-diff-first / cancel)
```

Branch on the user's response:
- `yes` — proceed to Phase 4.
- `review-diff-first` — run `token-fixer` in dry-run mode (it reports what it *would* change without doing it), present that, then re-prompt.
- `cancel` — stop, leave a written plan in `frontend/.claude/audit-reports/plan-<timestamp>.md` for later.

If `$ARGUMENTS` contained `auto-fix=true` AND the scope is entirely non-production (localhost/staging), skip the prompt and proceed directly.

### Phase 4 — Apply fixes

Delegate to `token-fixer` with the consolidated finding list filtered to mechanical-safe items only.

After the fixer returns its diff log:

- Summarise to the user: "Applied N fixes across M files. Skipped K as non-mechanical."
- If the project has a dev server running (check for a live page at the base URL — `list_pages` tool), wait for HMR/rebuild (pause 3–5 seconds), then go to Phase 5.
- If no dev server detected, tell the user: "Fixes are in source; rebuild and reload the app, then ask me to run Phase 5."

### Phase 5 — Runtime re-verify

Delegate to `runtime-auditor` again on the **same routes** audited in Phase 1.

Compare the new finding count to the Phase 1 count:

- Expected delta: Phase 1 count minus N (the number of mechanical fixes applied), plus or minus a small margin for fixes that cascaded or for findings that were actually state-dependent.
- If the new count is ≤ expected: report success with before/after numbers.
- If the new count > expected (new findings appeared): investigate — something in the fix broke something else. Report each new finding individually and recommend reverting those specific fixes if severity warrants.
- If any Phase 1 critical finding is still present in Phase 5: **the fix didn't land**. Diagnose: is it a build/cache issue, or did the fix target the wrong file? Report and stop.

### Final report

Produce a summary:

```
# Closed-loop audit complete

## Before (Phase 1)
- <N> findings (<C> critical, <M> major, <Mi> minor)
- <R> routes audited

## Fixes applied (Phase 4)
- <N> mechanical substitutions across <F> files
- <L> findings left for manual work (designer input or non-mechanical changes)

## After (Phase 5)
- <N> findings remain (<C> critical, <M> major, <Mi> minor)
- Net improvement: <delta>

## What's left
<list of non-mechanical findings, grouped by type>
1. <shared component that needs a real refactor>
2. <off-scale spacing value that needs a designer decision>
...

## Artifacts
- Runtime audit reports: frontend/.claude/audit-reports/runtime-<ts-before>.md, runtime-<ts-after>.md
- Diff log: frontend/.claude/audit-reports/fixes-<ts>.md
```

## Efficiency and safety rules

- **Never run this against production without explicit per-phase confirmation.** Production URLs detected (anything not localhost/staging) require `yes` at every phase boundary — not just once at the start.
- **Budget check.** If Phase 1 returns >500 findings, don't just barrel into Phase 3 fixing all of them. Recommend the user work through them in batches (e.g., "fix only critical findings this run, then re-run for majors").
- **Idempotency.** The workflow is safe to run repeatedly — Phase 5 of run 1 becomes Phase 1 of run 2. Fix → re-audit → fix → re-audit until clean.
- **Keep reports.** Write each phase's report to `frontend/.claude/audit-reports/` with timestamps. Over time the trend of these reports is a useful project-health metric.

## What this is *not*

- Not a replacement for design review. The workflow fixes mechanical violations; it does not decide whether a component *should* be a button or a link, whether spacing is *right* for a given layout, or whether the IA is sensible.
- Not a replacement for human QA. The auditor checks rule compliance; it does not notice that the copy is wrong, or that the feature doesn't actually work.
- Not infinite. Some things just need a designer, a PM, or a rewrite. The workflow makes that short-list visible; it does not shorten the list for you.
