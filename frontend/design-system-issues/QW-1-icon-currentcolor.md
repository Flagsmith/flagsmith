---
title: "Icon.tsx: Replace #1A2634 defaults with currentColor"
labels: ["design-system", "quick-win", "dark-mode", "icons"]
---

## Problem

~54 SVG icons in `Icon.tsx` default their fill to `#1A2634` (dark navy). On dark mode backgrounds (`#101628`), this makes the icons effectively invisible — dark icon on a dark background with near-zero contrast.

## Files

- `web/components/Icon.tsx` — 46 instances of `fill={fill || '#1A2634'}`, plus hardcoded `#1A2634` stroke in 3 paths

## Proposed Fix

Replace all instances of:

```tsx
fill={fill || '#1A2634'}
```

with:

```tsx
fill={fill || 'currentColor'}
```

Also update any hardcoded `stroke="#1A2634"` to `stroke={stroke || 'currentColor'}` or inherit from `currentColor`.

## Acceptance Criteria

- [ ] All icons are visible in both light and dark mode
- [ ] No hardcoded `#1A2634` colour values remain in `Icon.tsx`
- [ ] Icons that receive an explicit `fill` prop continue to render that colour correctly
- [ ] No visual regression in light mode

## Storybook Validation

Design System / Icons / Dark Mode Broken — verify all icons in the story render correctly on a dark background after the fix.

## Dependencies

None — this is a prerequisite for QW-2.

---
Part of the Design System Audit (#6606)
