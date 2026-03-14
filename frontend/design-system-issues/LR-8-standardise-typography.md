---
title: "Standardise typography usage across the codebase"
labels: ["design-system", "large-refactor", "typography"]
---

## Problem

A type scale (h1–h6, body sizes, weight tiers) exists in SCSS but is bypassed in 58+ places. Four related problems:

1. **Inline `fontSize` values** (58+ occurrences) — components set font sizes via `style={{ fontSize: '...' }}` instead of using the existing SCSS variables or utility classes.
2. **Fragmented weight system** — font weight is applied via two competing conventions: custom classes (`.font-weight-medium`) and Bootstrap utilities (`fw-bold`, `fw-semibold`). Both exist in the codebase simultaneously.
3. **Opacity-based muted text** — "subtle" or secondary text uses `opacity: 0.5` or similar rather than a semantic muted colour, which breaks in dark mode and fails contrast checks.
4. **No `Text` component** — there is nothing preventing future bypass of the type scale. A `Text` component may be warranted, but only if the migration itself reveals the need — not as a speculative abstraction.

## Files

- 58+ component files with inline `style={{ fontSize: '...' }}` — full list available via audit
- Components mixing `.font-weight-medium` and `fw-*` Bootstrap utilities
- Components using `opacity` for muted/secondary text

## Proposed Fix

1. Replace all 58 inline `fontSize` values with existing SCSS variables or utility classes
2. Pick one weight class system (Bootstrap `fw-*` is preferred — it is already present and tree-shakeable) and migrate all `.font-weight-*` usages
3. Replace opacity-based muted text with `$text-muted` / `colorTextSecondary` tokens
4. Introduce a `Text` component only if the migration demonstrates a repeated need — do not create it speculatively

## Acceptance Criteria

- [ ] No inline `fontSize` values remain in the migrated files
- [ ] A single font weight class system is in use (Bootstrap `fw-*`)
- [ ] All `.font-weight-*` custom classes are removed
- [ ] No opacity-based muted text remains — replaced with semantic colour tokens
- [ ] `npm run typecheck` and `npm run lint` pass

## Storybook Validation

- `Design System/Typography` — verify type scale renders correctly across all size and weight variants

## Dependencies

ME-10 (if that item covers the `$text-muted` token — confirm before starting step 3 to avoid conflicts)

---
Part of the Design System Audit (#6606)
