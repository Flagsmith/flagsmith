---
title: "Standardise off-grid spacing values"
labels: ["design-system", "medium-effort"]
---

## Problem

The design system uses an 8px base grid (`$spacer`) but numerous SCSS files use
off-grid values that break visual rhythm. The most common offenders:

### `5px` — 10+ occurrences (highest frequency)

| File | Usage |
|------|-------|
| `web/styles/project/_buttons.scss` | `padding: 0 5px` (btn--with-icon), `margin-left: 5px` (btn__icon) |
| `web/styles/project/_panel.scss` | `margin-left: 5px` |
| `web/styles/project/_tags.scss` | `margin-left: 5px` (3 occurrences) |
| `web/styles/project/_lists.scss` | `padding: 5px` (2 occurrences) |
| `web/styles/components/_chip.scss` | `padding: 5px 12px`, `margin-right: 5px` (4 occurrences) |
| `web/styles/components/_paging.scss` | `padding: 5px` |
| `web/styles/3rdParty/_hljs.scss` | `padding-bottom: 5px`, `margin-right: 5px` |

### `6px` — 3+ files

Found in `_variables.scss`, `_buttons.scss`, `_modals.scss`, `_FeaturesPage.scss`,
`_forms.scss`, `_metrics.scss`, `_chip.scss`, `_react-select.scss`,
`_tooltips.scss`, and `_hljs.scss`.

### Other off-grid values

| Value | Files |
|-------|-------|
| `3px` | `_switch.scss` (toggle position — intentional for centring), `_chip.scss`, `_react-select.scss`, `_utils.scss`, `_release-pipelines.scss`, `_feature-pipeline-status.scss`, scrollbar mixins |
| `15px` | `_hljs.scss`, `_tabs.scss` (line-height) |
| `19px` | `_icons.scss` (font-size) |

## Files

All SCSS files under `web/styles/` — primarily:

- `web/styles/components/_chip.scss` — highest density of `5px` usage
- `web/styles/project/_buttons.scss`
- `web/styles/project/_tags.scss`
- `web/styles/project/_lists.scss`
- `web/styles/project/_panel.scss`
- `web/styles/components/_paging.scss`
- `web/styles/3rdParty/_hljs.scss`

## Proposed Fix

### Phase 1 — Bulk replace `5px` with `4px`

`5px` is a single pixel off the 4px sub-grid. In almost all cases (margins,
padding), the visual difference is negligible but alignment with the grid
improves.

```bash
# Preview changes first
grep -rn ': 5px\| 5px' web/styles --include='*.scss'

# Apply (review each file individually — some 5px values may be intentional)
```

**Exceptions to review manually:**
- `_chip.scss` `.chip-sm` `padding: 5px 12px` — consider `4px 12px`
- `_buttons.scss` btn--with-icon `padding: 0 5px` — consider `0 4px`

### Phase 2 — Review `3px` values

Many `3px` values are positional offsets for centring (e.g. switch toggle
`left: 3px`, `top: 3px`). These are typically intentional and should not be
changed to `4px` without verifying the visual result. Review case by case.

### Phase 3 — Address `15px` and `19px`

- `_tabs.scss` `line-height: 15px` → consider `16px` (2 grid units)
- `_icons.scss` `font-size: 19px` → consider `20px` or `18px` depending on
  the icon's intended optical size

### Phase 4 — Introduce spacing tokens

Define spacing scale tokens to prevent future off-grid drift:

```scss
$space-0: 0;
$space-1: 4px;   // half grid
$space-2: 8px;   // 1 grid unit ($spacer)
$space-3: 12px;  // 1.5 grid units
$space-4: 16px;  // 2 grid units
$space-5: 20px;
$space-6: 24px;
$space-8: 32px;
$space-10: 40px;
$space-12: 48px;
```

## Verification

```bash
# Search for remaining off-grid values after changes
grep -rn '5px\|3px\|15px\|19px' web/styles --include='*.scss'

# Visual regression check — compare screenshots before/after
npm run storybook

# Build check
npm run build
```

## Acceptance Criteria

- [ ] No `5px` values remain in SCSS (replaced with `4px` or a spacing token)
- [ ] `3px` values reviewed — intentional positional offsets documented, others
      replaced
- [ ] `15px` and `19px` replaced with grid-aligned alternatives where appropriate
- [ ] No visual regressions in buttons, chips, tags, lists, or pagination
- [ ] Spacing tokens defined in `_variables.scss` for future use

---
Part of the Design System Audit (#6606)
