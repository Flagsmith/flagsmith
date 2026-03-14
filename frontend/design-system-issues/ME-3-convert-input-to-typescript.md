---
title: "Convert Input.js to TypeScript"
labels: ["design-system", "medium-effort"]
---

## Problem

`web/components/base/forms/Input.js` is a legacy class component at 231 lines. It handles multiple distinct input behaviours — text inputs, passwords (with toggle), search, checkboxes, and radio buttons — all within a single file with no TypeScript types. This makes it difficult to refactor safely, add new variants, or catch prop-related bugs at compile time.

## Files

- `web/components/base/forms/Input.js` — 231-line legacy class component with no TypeScript types

## Proposed Fix

Convert `Input.js` to a TypeScript functional component (`Input.tsx`). During the conversion, consider splitting out distinct variants via explicit props rather than implicit conditional logic:

- `type="password"` — includes the show/hide toggle
- `type="search"` — includes the clear/search icon
- `type="checkbox"` and `type="radio"` — may warrant separate typed interfaces

Ensure full TypeScript types are defined for all props. The conversion should produce identical visual and functional output — this is a type-safety and maintainability improvement, not a redesign.

## Acceptance Criteria

- [ ] `Input.js` converted to `Input.tsx` as a functional component
- [ ] Full TypeScript prop types defined (no `any`)
- [ ] Same visual output as before across all input variants (text, password, search, checkbox, radio)
- [ ] No runtime regressions in forms that use this component
- [ ] `npm run typecheck` passes with no new errors

## Storybook Validation

Not applicable — this is a type-safety refactor. Manual testing of all input variants in existing forms is sufficient.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
