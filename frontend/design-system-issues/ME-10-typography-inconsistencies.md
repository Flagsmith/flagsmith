---
title: "Typography inconsistencies — enforce the existing type scale"
labels: ["design-system", "medium-effort", "typography"]
---

## Problem

A type scale and weight system are defined in SCSS but are widely bypassed across the codebase. This results in visually inconsistent text sizing, weight, and colour, and introduces accessibility concerns from opacity-based "muted" text.

Specific issues found in the audit:

- **58 hardcoded inline `fontSize` values** in TSX files (13px: 17 instances, 12px: 12 instances, 11px: 7 instances, and more) — none of these reference the existing SCSS variables
- **Inconsistent font weight application** — 4 weight tiers (700, 600, 500, 400) applied ad-hoc, with `.font-weight-medium` competing against Bootstrap's `fw-bold`, `fw-semibold`, and `fw-normal`
- **9 inline `fontWeight` values** in TSX bypassing the class system entirely
- **Opacity-based muted text** — subtle/secondary text uses `opacity: 0.4–0.75` instead of a colour token, which fails WCAG contrast requirements when the background is not guaranteed to be white or dark
- **Minimal utility classes** — only `.text-small`, `.large-para`, `.font-weight-medium`, and `.bold-link` exist; most usage falls back to raw values
- **Semi-bold bug in `SuccessMessage`** — incorrect weight applied

## Files

- `web/` (TSX files broadly) — 58 hardcoded `fontSize` and 9 hardcoded `fontWeight` inline styles
- `web/styles/project/_typography.scss` — type scale variables exist but are underused
- `web/styles/project/_variables.scss` — `$text-muted` and `colorTextSecondary` tokens defined but bypassed
- `web/components/SuccessMessage.tsx` — semi-bold weight bug

## Proposed Fix

1. **Replace 58 hardcoded `fontSize` values** with existing SCSS variables or CSS utility classes. Define missing utility classes if a size has no corresponding class.
2. **Standardise on one weight class system** — choose between the existing `.font-weight-medium` pattern and Bootstrap's `fw-*` utilities; remove the other (or alias them). Apply consistently.
3. **Replace opacity-based muted text** with the colour token approach (`$text-muted` / `colorTextSecondary`) across all usages.
4. **Fix the semi-bold bug** in `SuccessMessage.tsx`.
5. Optionally expand utility classes to cover the most common size/weight combinations observed in the audit.

## Acceptance Criteria

- [ ] No hardcoded `fontSize` inline styles remain in TSX (use SCSS variables or utility classes)
- [ ] No hardcoded `fontWeight` inline styles remain in TSX (use utility classes)
- [ ] One font weight class system in use consistently throughout the codebase
- [ ] Opacity-based muted text replaced with colour token (`$text-muted` / `colorTextSecondary`)
- [ ] `SuccessMessage` semi-bold bug fixed
- [ ] All changes pass `npm run lint` and `npm run typecheck`
- [ ] No visual regression on key pages

## Storybook Validation

Design System / Typography — verify the type scale renders correctly at all sizes and weights in both light and dark mode. Muted/secondary text should meet WCAG AA contrast in both modes.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
