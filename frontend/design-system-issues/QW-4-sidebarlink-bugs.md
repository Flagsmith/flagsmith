---
title: "Fix SidebarLink hover and icon colour in dark mode"
labels: ["design-system", "quick-win", "bug", "dark-mode"]
issue: https://github.com/Flagsmith/flagsmith/issues/6868
pr: https://github.com/Flagsmith/flagsmith/pull/6871
---

## Problem

`SidebarLink.tsx` has three bugs affecting dark mode and hover behaviour.

## Scope (updated to match PR #6871)

| Bug | Before | After |
|-----|--------|-------|
| Copy-paste bug | `inactiveClassName={activeClassName}` — inactive links get active styling | `inactiveClassName={inactiveClassName}` |
| Icon colour not controllable by CSS | `<Icon fill='#767D85' />` — inline fill overrides CSS utility classes | `<span className='text-muted'><Icon /></span>` — uses `currentColor` via CSS |
| Non-existent CSS hover classes | References hover classes that don't exist in the stylesheet | Replaced with working CSS hover classes |

The original audit identified bugs 1 and 2. The PR also discovered that the hover CSS classes referenced in the component didn't actually exist, so the hover state was broken entirely.

## Files

- `web/components/navigation/SidebarLink.tsx`

## Verification

```bash
# Type check
npm run typecheck

# Lint
npx eslint --fix web/components/navigation/SidebarLink.tsx

# Visual check:
# - Active item has primary colour text and icon
# - Inactive items have muted text and icon
# - Hover state changes icon/text to primary colour
# - Dark mode renders all states correctly
```

## Acceptance Criteria

- [x] `inactiveClassName` prop receives the correct variable
- [x] No hardcoded `fill` prop on the `<Icon>` component
- [x] Hover classes reference existing CSS
- [ ] `npm run typecheck` passes
- [ ] Dark mode sidebar renders correctly

---
Part of the Design System Audit (#6606)
