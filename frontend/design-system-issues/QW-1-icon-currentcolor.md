---
title: "Replace hardcoded icon fill with currentColor"
labels: ["design-system", "quick-win", "dark-mode", "accessibility"]
issue: https://github.com/Flagsmith/flagsmith/issues/6869
pr: https://github.com/Flagsmith/flagsmith/pull/6870
---

## Problem

`Icon.tsx` hardcodes fill colours on ~57 inline SVG icons, making them invisible or wrong in dark mode. The background in dark mode is `#101628`, and icons using `#1A2634` have a contrast ratio of ~1.1:1.

This is the single highest-priority design system issue, affecting the majority of icons across the entire UI.

## Scope (updated to match PR #6870)

The original audit found 41 instances of `fill={fill || '#1A2634'}`. The PR expanded scope to cover **all hardcoded fill patterns** (~57 total):

| Pattern | Count | Fix |
|---------|-------|-----|
| `fill={fill \|\| '#1A2634'}` | 41 | → `fill={fill \|\| 'currentColor'}` |
| `fill={fill \|\| '#9DA4AE'}` | several | → `fill={fill \|\| 'currentColor'}` |
| `fill={fill \|\| '#656D7B'}` | several | → `fill={fill \|\| 'currentColor'}` |
| `fill={fill \|\| '#000000'}` | 1 | → `fill={fill \|\| 'currentColor'}` |
| `fill={fill \|\| 'white'}` (plus icon) | 1 | → `fill={fill \|\| 'currentColor'}` |
| `fill={fill}` with no fallback | several | → `fill={fill \|\| 'currentColor'}` |
| Hardcoded fills on SVG elements (`github`, `pr-draft`) | 2 | → use `fill` prop |

Additionally, **10 unused icons were removed** as part of the cleanup.

## Files

- `web/components/Icon.tsx` — single file change

## Verification

```bash
# Confirm no remaining hardcoded hex fills
grep -cE "fill=\{fill \|\| '#[0-9a-fA-F]" web/components/Icon.tsx
# Expected: 0

# Type check
npm run typecheck

# Visual check in Storybook (light + dark mode)
npm run storybook
```

## Acceptance Criteria

- [x] Zero instances of hardcoded hex fills remain in `Icon.tsx`
- [x] All icon SVGs default to `currentColor` when no explicit fill is passed
- [x] 10 unused icons removed
- [ ] `npm run typecheck` passes
- [ ] Icons are visible in both light and dark mode
- [ ] Icons that receive an explicit `fill` prop still render with that colour

---
Part of the Design System Audit (#6606)
