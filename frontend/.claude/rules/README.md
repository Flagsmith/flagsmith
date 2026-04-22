# Flagsmith design system rules

This directory is the source of truth for the Flagsmith design system as applied to the frontend. It is read by:

- Human contributors designing or editing visual code.
- The `design-auditor`, `token-fixer`, and `runtime-auditor` subagents (`frontend/.claude/agents/`).
- The slash commands `/audit-component`, `/audit-scope`, `/audit-runtime`, `/audit-app`, `/fix-tokens`, `/fix-app` (`frontend/.claude/commands/`).

## When to read what

**Always** — `design-tokens.md`. The token map underpins everything else.

**Any visual change** — `color.md`, `typography.md`, `spacing.md`, `anti-patterns.md`.

**Building or editing a component** — `components.md` (buttons, inputs, tables, cards, modals, tabs, etc.), plus `states.md` (hover, active, loading, empty, error, disabled, selected).

**Page-level work or large refactors** — `composition.md` (page title row, section anatomy, heading + descriptor, page templates).

**Accessibility review** — `accessibility.md`. Non-negotiable WCAG AA floor.

**Specific concerns**:
- Transitions, durations, easings — `motion.md`.
- Tables, charts, KPI tiles — `data-viz.md`.
- Breakpoints, mobile, tablet, sidebar reflow — `responsive.md`.
- Extra-compact / comfortable layouts — `density.md`.
- Copy tone, case, descriptor length — `copy.md`.

**Planning token / scale work** — `ROADMAP.md`. Lists known gaps and what's deliberately out of scope.

## Token consumption — the one file per layer

- **SCSS / CSS** — use `var(--color-*)`, `var(--radius-*)`, `var(--duration-*)`, `var(--easing-*)` directly. Defined in `frontend/web/styles/_tokens.scss` (auto-generated).
- **TSX / JSX** — import the typed named exports from `frontend/common/theme/tokens.ts` (auto-generated alongside the SCSS). Do not write raw `var(--color-*)` strings in JSX. See `design-tokens.md` §"Consuming tokens from TS / JSX" for the full list.
- **Never hand-edit** either generated file. The source of truth is `frontend/common/theme/tokens.json`; regenerate with `npm run generate:tokens`.

## The hierarchy (repeated because it matters)

1. **Semantic CSS custom properties** — `var(--color-surface-default)`, `var(--color-text-default)`, `var(--radius-md)`. Reach here first. Auto-flips light ↔ dark.
2. **SCSS semantic vars** — `$primary`, `$success`, `$body-bg-dark`. Acceptable in SCSS where a CSS var doesn't exist yet; don't mix with CSS vars in the same file.
3. **Primitives** — `$slate-600`, `$purple-500`. Token-layer authoring only. Never in components.
4. **Raw values** — hex, off-scale px, decimal alpha. Forbidden.

## Dual-mode reminder

Light is the default. Dark mode is applied by `web/project/darkMode.ts` which puts `.dark` on `<body>` and `data-bs-theme="dark"` on `<html>` (persisted in `localStorage.dark_mode`). Every colour, every surface, every border must survive both modes — the semantic tokens handle this automatically. Writing `.dark .my-component { ... }` in component SCSS is almost always a sign the token layer is wrong; fix the token, not the component.
