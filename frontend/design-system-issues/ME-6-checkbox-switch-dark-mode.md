---
title: "Checkbox and switch dark mode states"
labels: ["design-system", "medium-effort", "dark-mode"]
---

## Problem

Two related dark mode gaps exist in form controls:

1. `Switch.tsx` uses hardcoded colours for its sun and moon icons rather than CSS variables or `currentColor`. In dark mode the icons do not adapt correctly.
2. Form checkboxes and radio buttons (rendered via `Input.js`) have no `.dark` overrides in the SCSS. Their custom styles render with light mode colours in dark mode.

## Files

- `web/components/base/Switch.tsx` — hardcoded colours for sun/moon icons
- `web/components/base/forms/Input.js` — no dark mode overrides for checkbox/radio custom styles
- `web/styles/project/_forms.scss` (or equivalent) — location to add `.dark` checkbox/radio overrides

## Proposed Fix

1. In `Switch.tsx`, replace hardcoded colour values for the sun and moon icons with `currentColor` or CSS custom properties so they inherit from the surrounding dark mode context.
2. In the relevant SCSS file, add `.dark` overrides for the custom checkbox and radio button styles (border colour, background, checked state fill, focus ring).

## Acceptance Criteria

- [ ] `Switch` component sun/moon icons display correctly in both light and dark mode
- [ ] Checkboxes render correctly in dark mode (unchecked, checked, indeterminate, disabled states)
- [ ] Radio buttons render correctly in dark mode (unchecked, checked, disabled states)
- [ ] No visual regression in light mode for any of the above

## Storybook Validation

Design System / Forms / Switch — toggle dark mode and verify sun/moon icon colours.
Design System / Forms / Checkbox and Radio — toggle dark mode and verify all states.

## Dependencies

None. (ME-3 converts `Input.js` to TypeScript, but dark mode SCSS fixes can land independently of that.)

---
Part of the Design System Audit (#6606)
