---
title: "Define typography tokens and standardise type scale"
labels: ["design-system", "large-refactor", "tokens"]
status: DRAFT
---

## Problem

The codebase lacks formal typography tokens. Font weights, sizes, and
line-heights are hardcoded inline or scattered across SCSS files with no
centralised scale.

### Specific issues

1. **No `$font-weight-*` tokens** — there is no `$font-weight-semibold`,
   `$font-weight-bold`, or `$font-weight-regular` variable. Instead,
   `fontWeight: 600` is hardcoded in multiple files:
   - `web/components/navigation/AccountDropdown.tsx`
   - `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx`
   - `web/components/pages/admin-dashboard/components/OrganisationUsageTable.tsx`

2. **Invalid CSS value** — `web/components/messages/SuccessMessage.tsx:44`
   contains `fontWeight: 'semi-bold'` which is not a valid CSS value. Browsers
   silently ignore it, so the intended semibold weight is never applied.

3. **50+ inline style overrides** — the admin dashboard pages alone contain 50+
   instances of inline `style={{ fontWeight: ..., fontSize: ... }}` that bypass
   the SCSS type scale entirely.

4. **h1-h6 scale exists but is bypassed** — `web/styles/project/_type.scss`
   defines heading styles, but components frequently override them with inline
   styles or ad hoc classes.

5. **Off-scale line-heights** — at least 4 line-height values in use that don't
   align with the base grid (`1.3`, `1.15`, `18px`, `22px`).

6. **No responsive typography** — font sizes are fixed pixel values with no
   fluid scaling or breakpoint adjustments.

## Files

- `web/styles/_variables.scss` — where `$font-weight-*` tokens should be defined
- `web/styles/_tokens.scss` — where CSS custom property typography tokens should
  live
- `web/styles/project/_type.scss` — existing heading and body type scale
- `web/components/navigation/AccountDropdown.tsx` — hardcoded `fontWeight: 600`
- `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx`
  — hardcoded `fontWeight: 600`
- `web/components/pages/admin-dashboard/components/OrganisationUsageTable.tsx` —
  hardcoded `fontWeight: 600`
- `web/components/messages/SuccessMessage.tsx` — invalid `fontWeight: 'semi-bold'`

## Proposed Fix

### Step 1 — Define font weight tokens

Add to `_variables.scss`:

```scss
$font-weight-regular:  400;
$font-weight-medium:   500;
$font-weight-semibold: 600;
$font-weight-bold:     700;
```

### Step 2 — Define CSS custom property typography tokens

Add to `_tokens.scss`:

```scss
:root {
  // Font weights
  --font-weight-regular:  #{$font-weight-regular};
  --font-weight-medium:   #{$font-weight-medium};
  --font-weight-semibold: #{$font-weight-semibold};
  --font-weight-bold:     #{$font-weight-bold};

  // Font sizes
  --font-size-xs:   0.75rem;   // 12px
  --font-size-sm:   0.8125rem; // 13px
  --font-size-base: 0.875rem;  // 14px
  --font-size-md:   1rem;      // 16px
  --font-size-lg:   1.125rem;  // 18px
  --font-size-xl:   1.25rem;   // 20px
  --font-size-2xl:  1.5rem;    // 24px
  --font-size-3xl:  2rem;      // 32px

  // Line heights
  --line-height-tight:  1.25;
  --line-height-normal: 1.5;
  --line-height-loose:  1.75;
}
```

### Step 3 — Add TypeScript exports

Add to `common/theme/tokens.ts`:

```ts
export const fontWeightRegular = 'var(--font-weight-regular, 400)'
export const fontWeightMedium = 'var(--font-weight-medium, 500)'
export const fontWeightSemibold = 'var(--font-weight-semibold, 600)'
export const fontWeightBold = 'var(--font-weight-bold, 700)'
```

### Step 4 — Replace hardcoded values

For each file with `fontWeight: 600`:
```tsx
// Before
style={{ fontWeight: 600 }}

// After
import { fontWeightSemibold } from 'common/theme'
style={{ fontWeight: fontWeightSemibold }}
```

Or preferably, use a CSS class:
```scss
.text-semibold { font-weight: var(--font-weight-semibold); }
```

### Step 5 — Fix the invalid CSS value

In `SuccessMessage.tsx:44`, change `fontWeight: 'semi-bold'` to
`fontWeight: 'var(--font-weight-semibold, 600)'` (or use a CSS class).

### Step 6 — Standardise line-heights

Replace off-scale line-height values (`1.3`, `1.15`, `18px`, `22px`) with the
nearest token from the defined scale.

## Acceptance Criteria

- [ ] `$font-weight-regular`, `$font-weight-medium`, `$font-weight-semibold`,
      and `$font-weight-bold` are defined in `_variables.scss`
- [ ] CSS custom properties for font weights, sizes, and line-heights are defined
      in `_tokens.scss`
- [ ] TypeScript exports exist in `common/theme/tokens.ts`
- [ ] Zero hardcoded `fontWeight: 600` or `fontWeight: 'bold'` in TSX files —
      all use tokens
- [ ] `fontWeight: 'semi-bold'` bug in `SuccessMessage.tsx` is fixed
- [ ] Off-scale line-height values are replaced with token references
- [ ] `npm run typecheck` and `npm run build` pass
- [ ] No visual regressions — typography looks identical before and after

## Dependencies

- Related to **LR-2** (Semantic colour tokens) — follows the same 3-layer token
  architecture pattern
- Related to **LR-6** (Colour primitives) — the primitive layer concept applies
  to typography as well
- Can proceed independently — no hard blockers

---
Part of the Design System Audit (#6606)
