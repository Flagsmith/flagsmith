---
title: "Fix invalid fontWeight: 'semi-bold' in SuccessMessage"
labels: ["design-system", "quick-win", "typography"]
---

## Problem

Both `SuccessMessage.tsx` and `SuccessMessage.js` use `fontWeight: 'semi-bold'` as an inline style. This is not a valid CSS `font-weight` value — the correct string value is `'600'` (a numeric string) or the number `600`. Browsers silently ignore invalid `font-weight` values, meaning the text renders at the default weight (400) instead of the intended semi-bold weight.

## Files

- `web/components/messages/SuccessMessage.tsx` — `fontWeight: 'semi-bold'`
- `web/components/SuccessMessage.js` — `fontWeight: 'semi-bold'`

## Proposed Fix

Replace the invalid string value with the numeric equivalent:

```tsx
// Before
fontWeight: 'semi-bold'

// After
fontWeight: 600
```

If either file is used as the canonical source and the other is a duplicate or legacy version, consider whether `SuccessMessage.js` can be removed in favour of the TypeScript version as a follow-up.

## Acceptance Criteria

- [ ] `SuccessMessage` text renders at semi-bold (600) weight in the browser
- [ ] No `fontWeight: 'semi-bold'` string remains in either file
- [ ] No visual regression — the change should only make the intended weight actually apply

## Storybook Validation

Design System / Typography / Weight And Style Usage — the Bugs Found section should show `SuccessMessage` rendering at the correct weight after the fix.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
