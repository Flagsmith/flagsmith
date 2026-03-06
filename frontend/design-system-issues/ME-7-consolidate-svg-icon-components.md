---
title: "Consolidate 23 separate SVG icon components"
labels: ["design-system", "medium-effort", "icons"]
---

## Problem

23 SVG icon components exist outside the canonical `<Icon name="..." />` API, spread across 3 directories. These components bypass the shared icon system, have no consistent pattern for props, sizing, or colour, and cannot be themed centrally (e.g. dark mode `currentColor` fix in `Icon.tsx` does not apply to them).

The 23 components are distributed across:

- `web/components/svg/` — 19 navigation/sidebar icons
- `web/components/base/icons/` — 2 icons (`GithubIcon`, `GitlabIcon`)
- `web/components/` — 2 icons (`IdentityOverridesIcon`, `SegmentOverridesIcon`)

## Files

- `web/components/svg/` — 19 SVG components outside the icon system
- `web/components/base/icons/GithubIcon.tsx` — standalone icon
- `web/components/base/icons/GitlabIcon.tsx` — standalone icon
- `web/components/IdentityOverridesIcon.tsx` — standalone icon
- `web/components/SegmentOverridesIcon.tsx` — standalone icon
- `web/components/Icon.tsx` — the canonical icon component these should integrate with

## Proposed Fix

Option A (minimal): Add each of the 23 icons to the `Icon.tsx` switch statement as named entries, keeping the inline SVG approach.

Option B (preferred, long-term): Extract `Icon.tsx`'s existing inline SVGs into individual files and merge all 23 external icons into the same file-based structure. This makes the icon library easier to extend and avoids a monolithic switch statement.

Whichever option is chosen, the result must be:
- All 23 icons accessible via `<Icon name="..." />`
- Consistent `currentColor` usage so icons inherit colour from context
- Consistent sizing via the existing size prop

## Acceptance Criteria

- [ ] All 23 standalone SVG components accessible via `<Icon name="..." />`
- [ ] Icons inherit colour via `currentColor` (no hardcoded fill/stroke values)
- [ ] Consistent size prop behaviour across all icons
- [ ] Original call sites updated to use `<Icon name="..." />`
- [ ] Original standalone files deleted

## Storybook Validation

Design System / Icons / Separate SVG Components — all 23 icons should appear in the icon gallery story. Toggle dark mode and verify all icons adapt via `currentColor`.

## Dependencies

None. However, ME-4 (toast dark mode) prefers this to be complete first before replacing toast inline SVGs.

---
Part of the Design System Audit (#6606)
