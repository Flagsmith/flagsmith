---
title: "Fix 9 icons with hardcoded fills that ignore the fill prop"
labels: ["design-system", "quick-win", "dark-mode", "icons"]
---

## Problem

9 icons in `Icon.tsx` have fill colours baked directly into their SVG paths. Because these fills are hardcoded in the markup rather than applied via the `fill` prop, passing a `fill` value to the `<Icon>` component has no effect. Several of these are invisible in dark mode; others may be intentional brand colours.

## Files

- `web/components/Icon.tsx` — the following icon definitions contain hardcoded fills:

| Icon | Hardcoded Colour | Issue |
|------|-----------------|-------|
| `github` | `#1A2634` | Invisible in dark mode |
| `pr-draft` | `#1A2634` | Invisible in dark mode |
| `google` | Multi-colour brand colours | Intentional — keep as-is |
| `link` | `rgb(104, 55, 252)` | Should use `currentColor` |
| `pr-merged` | `#8957e5` | GitHub purple — intentional? Needs decision |
| `issue-closed` | `#8957e5` | GitHub purple — intentional? Needs decision |
| `issue-linked` | `#238636` | GitHub green — intentional? Needs decision |
| `pr-linked` | `#238636` | GitHub green — intentional? Needs decision |
| `pr-closed` | `#da3633` | GitHub red — intentional? Needs decision |

## Proposed Fix

Apply changes based on intent:

**Clear fixes (no decision needed):**
- `github`: Replace hardcoded `#1A2634` path fills with `fill={fill || 'currentColor'}`
- `pr-draft`: Replace hardcoded `#1A2634` path fills with `fill={fill || 'currentColor'}`
- `link`: Replace `rgb(104, 55, 252)` with `fill={fill || 'currentColor'}` so it inherits brand purple from CSS context

**Requires team decision:**
- `pr-merged`, `issue-closed`, `issue-linked`, `pr-linked`, `pr-closed`: Decide whether to keep the GitHub brand status colours (which are contextually meaningful) or replace with `currentColor` for theme consistency. If keeping brand colours, document this as intentional in a code comment.

**Keep as-is:**
- `google`: Multi-colour brand logo — intentional, no change needed.

## Acceptance Criteria

- [ ] `github` and `pr-draft` icons are visible in dark mode
- [ ] `link` icon colour is controlled by CSS context / the `fill` prop
- [ ] A decision is recorded (in code comments or in this issue) for each GitHub status icon
- [ ] `google` icon is unchanged
- [ ] No unintended visual regressions in light mode

## Storybook Validation

Design System / Icons / Hardcoded Fills — verify each affected icon renders correctly in both light and dark backgrounds after the fix.

## Dependencies

Should be done after or alongside QW-1 for consistency, but can be worked independently.

---
Part of the Design System Audit (#6606)
