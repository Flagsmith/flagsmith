---
title: "Full dark mode theme audit"
labels: ["design-system", "large-refactor", "dark-mode"]
---

## Problem

Only 48 `.dark` CSS selectors exist across the entire stylesheet. Many feature areas have zero dark mode coverage. Known problem areas include:

- **Feature pipeline visualisation** — white circles and grey lines on dark background (invisible)
- **Admin dashboard charts** — light-mode-only colours hardcoded in chart config
- **Integration cards** — no `.dark` overrides, renders with light background
- **Numerous inline styles** — `color`, `background`, and `border` values hardcoded with light-mode hex values, unreachable by any CSS selector

This is the umbrella issue. All quick-win (QW) and medium-effort (ME) dark mode items from the audit feed into it.

## Files

- `web/styles/` — 48 `.dark` rules across 29 files (full list in audit report)
- Any component with inline `style={{ color: '#...' }}` or `style={{ background: '#...' }}` using light-mode-only values

## Proposed Fix

Systematic page-by-page dark mode audit:

1. For each page/feature area: toggle dark mode, take a screenshot, identify contrast failures
2. For each failure: replace hardcoded values with `currentColor`, CSS custom properties, or `.dark` overrides as appropriate
3. Prefer CSS custom properties (LR-2) over new `.dark` selectors — new `.dark` selectors should only be added as a stopgap
4. Document coverage gaps as they are discovered

This issue tracks the umbrella effort. Sub-tasks per feature area should be filed separately and linked here.

## Acceptance Criteria

- [ ] Every top-level page has been audited in dark mode
- [ ] All critical (P0) contrast failures are resolved
- [ ] Feature pipeline visualisation renders correctly in dark mode
- [ ] Admin dashboard charts render correctly in dark mode
- [ ] Integration cards render correctly in dark mode
- [ ] No inline styles with light-mode-only hardcoded colours remain in audited areas

## Storybook Validation

- `Design System/Dark Mode Issues/Dark Mode Implementation Patterns` — patterns reference for contributors

## Dependencies

All QW and ME dark mode items from the audit contribute to this issue. LR-2 (semantic tokens) will significantly reduce the per-component effort once adopted.

---
Part of the Design System Audit (#6606)
