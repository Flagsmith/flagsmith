---
title: "Icon.tsx — break up monolithic component"
labels: ["design-system", "large-refactor", "icons"]
---

## Problem

`Icon.tsx` is 1,543 lines containing 70+ inline SVG definitions in a single switch statement. It is the largest component in the codebase. One icon (`paste`) is declared in the `IconName` type but has no implementation — it falls through the switch silently.

## Files

- `web/components/Icon.tsx` — monolithic switch statement with all SVG inline, 1,543 lines

## Proposed Fix

Extract each icon into its own file under `web/components/icons/`. Create an `IconMap` that lazy-loads icons by name. Keep the `<Icon name="..." />` API unchanged so no call sites need to change.

The `paste` icon must either be implemented or removed from the `IconName` type.

## Acceptance Criteria

- [ ] Each icon lives in its own file under `web/components/icons/`
- [ ] The `<Icon name="..." />` public API is unchanged
- [ ] `paste` is either implemented or removed from `IconName`
- [ ] Bundle size is not increased (verify with bundle analyser)
- [ ] All existing icon usages render correctly

## Storybook Validation

Browse the existing icon story and confirm all icons render after the refactor.

## Dependencies

QW-1 (fix `currentColor` defaults first — icons must default to `currentColor` before extraction to avoid baking in the wrong fill)

---
Part of the Design System Audit (#6606)
