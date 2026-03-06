---
title: "Unify dropdown implementations"
labels: ["design-system", "medium-effort"]
---

## Problem

4 different dropdown patterns exist in the codebase with no clear guidance on when to use each. This leads to inconsistent behaviour, duplicated positioning logic, and difficulty maintaining dropdown-related bugs in one place.

The 4 patterns are:

1. `base/DropdownMenu.tsx` — icon-triggered action menu (the canonical pattern)
2. `base/forms/ButtonDropdown.tsx` — split button dropdown
3. `navigation/AccountDropdown.tsx` — duplicates `DropdownMenu` positioning logic rather than reusing it
4. `segments/Rule/components/EnvironmentSelectDropdown.tsx` — form-integrated dropdown

## Files

- `web/components/base/DropdownMenu.tsx` — canonical action menu
- `web/components/base/forms/ButtonDropdown.tsx` — split button variant
- `web/components/navigation/AccountDropdown.tsx` — duplicates positioning logic from DropdownMenu
- `web/components/segments/Rule/components/EnvironmentSelectDropdown.tsx` — form-integrated variant

## Proposed Fix

1. Standardise on `DropdownMenu` for all action menus.
2. Refactor `AccountDropdown` to use `DropdownMenu` as its base, removing the duplicated positioning logic.
3. Document when to use `ButtonDropdown` vs `DropdownMenu` (e.g. in a Storybook story description or inline JSDoc).
4. Assess whether `EnvironmentSelectDropdown` can use an existing base or whether a documented form-dropdown pattern is needed.

## Acceptance Criteria

- [ ] `AccountDropdown` refactored to use `DropdownMenu` as its base
- [ ] No duplicated dropdown positioning logic between components
- [ ] Consistent dropdown behaviour (keyboard navigation, close on outside click) across all usages
- [ ] Documentation added (Storybook description or JSDoc) clarifying when to use each dropdown variant

## Storybook Validation

Design System / Navigation / Account Dropdown — verify dropdown opens, positions correctly, and closes on outside click in both light and dark mode.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
