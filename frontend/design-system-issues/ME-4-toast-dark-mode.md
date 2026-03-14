---
title: "Toast notifications — add dark mode support"
labels: ["design-system", "medium-effort", "dark-mode"]
---

## Problem

Toast notifications (`web/project/toast.tsx`) have no dark mode styles. In dark mode, toasts render with light mode colours, making them difficult to read. Additionally, the inline SVGs used for success and danger icons use hardcoded colour values rather than referencing design tokens or the shared `Icon` component, making them impossible to theme correctly.

## Files

- `web/project/toast.tsx` — no dark mode styles, hardcoded SVG colours for success/danger icons

## Proposed Fix

1. Add `.dark .toast-message` CSS overrides to give toasts an appropriate dark mode appearance with correct contrast.
2. Replace the hardcoded inline SVGs for success and danger icons with the shared `<Icon>` component (available after ME-7 lands, or in parallel if Icon already supports these).

## Acceptance Criteria

- [ ] Toast notifications are readable in dark mode with correct contrast ratios
- [ ] Success and danger toast icons display correctly in both light and dark mode
- [ ] No visual regression in light mode

## Storybook Validation

Not applicable — toasts are triggered imperatively. Manual testing in both light and dark mode is required by opening any flow that triggers a success or error toast (e.g. creating a feature, deleting a flag).

## Dependencies

ME-7 (Consolidate SVG icon components) — preferred before replacing inline SVGs, but dark mode CSS fixes can land independently.

---
Part of the Design System Audit (#6606)
