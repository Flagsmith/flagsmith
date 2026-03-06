---
title: "Button variant dark mode gaps"
labels: ["design-system", "medium-effort", "dark-mode"]
---

## Problem

Three button variants — `btn-tertiary`, `btn-danger`, and `btn--transparent` — have no `.dark` mode overrides in the stylesheet, despite the corresponding dark mode variables already being defined. This means these buttons render with light mode colours in dark mode, causing potential contrast and readability issues.

## Files

- `web/styles/project/_buttons.scss` — missing `.dark` overrides for `btn-tertiary`, `btn-danger`, and `btn--transparent`
- `web/styles/project/_variables.scss` — dark mode variables already defined at lines 137–144 (`$btn-tertiary-bg-dark`, etc.) but unused

## Proposed Fix

Add `.dark` selectors in `_buttons.scss` that reference the existing dark mode variables from `_variables.scss`. No new variables need to be created — the work is purely wiring up what already exists.

Example pattern to follow:

```scss
.dark {
  .btn-tertiary {
    background-color: $btn-tertiary-bg-dark;
    color: $btn-tertiary-color-dark;
    border-color: $btn-tertiary-border-dark;
  }

  .btn-danger {
    // add dark overrides
  }

  .btn--transparent {
    // add dark overrides
  }
}
```

## Acceptance Criteria

- [ ] `btn-tertiary` renders correctly in both light and dark mode
- [ ] `btn-danger` renders correctly in both light and dark mode
- [ ] `btn--transparent` renders correctly in both light and dark mode
- [ ] No new SCSS variables introduced — only existing dark mode variables used
- [ ] No other button variants regressed

## Storybook Validation

Design System / Buttons / Dark Mode Gaps — toggle dark mode in Storybook and confirm all three variants display with correct colours and contrast.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
