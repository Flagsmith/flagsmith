---
title: "Define a formal colour palette"
labels: ["design-system", "large-refactor", "colours"]
---

## Problem

There is no formal, systematic colour palette. Five distinct problems compound each other:

1. **Inverted tonal scale** — `$primary400` (`#956CFF`) is lighter than `$primary` (`#6837FC`), reversing the conventional lower-number-is-lighter scale and making scale usage unpredictable.
2. **Alpha colour RGB mismatches** — `$primary-alfa-*` uses RGB `(149, 108, 255)` but `$primary` is `(104, 55, 252)`. The same mismatch exists for `$danger` and `$warning` alpha variants. Alpha colours do not derive from their solid counterparts.
3. **30+ orphan hex values** — hardcoded hex values in components that are not in `_variables.scss`. The most prevalent are `#9DA4AE` (52 usages) and `#656D7B` (44 usages).
4. **Missing scale steps** — no `$danger600`, `$success700`, `$info400`, `$warning200` and other mid-range steps, forcing components to reach for the nearest available step or hardcode a value.
5. **No grey scale** — greys are named ad hoc (`$text-icon-grey`, `$bg-light200`, `$footer-grey`) with no systematic neutral scale.

## Files

- `web/styles/_variables.scss` — current palette definitions with the above inconsistencies
- All components with hardcoded hex values not referenced in `_variables.scss`

## Proposed Fix

Define a formal primitive palette:

- Numbered tonal scales (50–900) per hue, where a lower number always means a lighter shade
- Alpha variants derived from the same RGB as their solid counterpart
- A systematic grey/neutral scale (e.g. `$grey50` through `$grey900`) replacing ad hoc names
- Every orphan hex value mapped to a palette token or removed

The palette definition should be implemented as SCSS variables and CSS custom properties. If a utility-class framework is adopted in the future, the palette can be mapped to it at that point.

## Acceptance Criteria

- [ ] All hue scales follow the lower-number-is-lighter convention (50–900)
- [ ] All alpha variants are derived from the correct RGB of their solid colour
- [ ] A systematic neutral/grey scale is defined
- [ ] All 30+ orphan hex values are replaced with palette tokens (or documented as intentional one-offs)
- [ ] Missing scale steps are added where components need them
- [ ] `npm run lint` passes (no SCSS errors)

## Storybook Validation

- `Design System/Colours/Palette Audit` — four stories covering: tonal scales, alpha variants, neutral scale, and orphan resolution

## Dependencies

This is a prerequisite for LR-2 (semantic colour tokens cannot reference a palette that does not exist yet).

---
Part of the Design System Audit (#6606)
