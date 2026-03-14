---
title: "Full dark mode audit pass across all SCSS files"
labels: ["design-system", "large-refactor", "dark-mode"]
status: DRAFT
---

## Problem

Dark mode is implemented through three parallel mechanisms that overlap
inconsistently, leaving large gaps in coverage.

### Three parallel dark mode mechanisms

1. **`.dark` CSS class on `<body>`** — toggled by `web/project/darkMode.ts` via
   `document.body.classList.add('dark')`. Used by 41 `.dark {}` blocks across 29
   SCSS files. This is the primary mechanism for component-level dark overrides.

2. **`data-bs-theme="dark"` attribute on `<html>`** — also set by `darkMode.ts`
   via `document.documentElement.setAttribute('data-bs-theme', 'dark')`. Despite
   being set, only `_tokens.scss` and Bootstrap's own variables respond to it.
   Almost no custom SCSS uses this selector.

3. **`getDarkMode()` runtime checks in JavaScript** — 10 files call
   `getDarkMode()` from `web/project/darkMode.ts` to conditionally apply inline
   styles or class names at render time:
   - `web/components/tags/Tag.tsx`
   - `web/components/CompareIdentities.tsx`
   - `web/components/CompareEnvironments.js`
   - `web/components/segments/Rule/components/RuleConditionValueInput.tsx`
   - `web/components/base/select/multi-select/InlineMultiValue.tsx`
   - `web/components/base/select/multi-select/CustomOption.tsx`
   - `web/components/feature-page/FeatureNavTab/CodeReferences/components/RepoSectionHeader.tsx`
   - `web/components/DarkModeSwitch.tsx`

   This approach re-renders components when dark mode changes only if the
   component re-mounts, creating flash-of-wrong-theme bugs.

### Coverage gaps

- **41 `.dark` blocks exist across 29 files** — but the codebase has 60+ SCSS
  files, meaning roughly half have no dark overrides at all.
- **Toast** — zero dark mode styles (`_toast.scss` has no `.dark` block)
- **Buttons** — `btn-tertiary`, `btn-danger`, `btn--transparent` have no dark
  overrides. `btn--outline` hardcodes `background: white`.
- **Forms** — `input:read-only` hardcodes `#777` with no dark override. Textarea
  border uses `border-color: $input-bg-dark` making it invisible. Checkbox
  focus/hover/disabled states missing in dark.
- **Icons** — 41 icons default to `fill: #1A2634`, invisible on dark background
  `#101628`.

## Files

- `web/project/darkMode.ts` — dark mode toggle implementation (sets both `.dark`
  class and `data-bs-theme` attribute)
- `web/styles/_tokens.scss` — semantic tokens with `.dark` overrides (drafted)
- `web/styles/_variables.scss` — colour variables including dark variants
- All SCSS files under `web/styles/` (60+ files)
- 10 TSX/JS files that call `getDarkMode()`

## Proposed Fix

### Step 1 — Unify on a single mechanism

Choose CSS custom properties + `.dark` class as the single mechanism.
`data-bs-theme` should be kept only for Bootstrap compatibility but not used in
custom SCSS. `getDarkMode()` runtime checks should be eliminated.

### Step 2 — Audit every SCSS file for dark coverage

For each SCSS file under `web/styles/`:
1. Check if it defines colours, backgrounds, borders, or shadows
2. If yes, verify a `.dark` override exists
3. If no `.dark` override, add one using semantic tokens from `_tokens.scss`

Priority order (by user impact):
1. `_toast.scss` — no dark styles at all
2. `_buttons.scss` — tertiary, danger, transparent variants
3. `_input.scss` — read-only, focus ring, textarea border
4. `_switch.scss` — focus/hover/disabled states
5. `_chip.scss` — inconsistent dark handling
6. Remaining files

### Step 3 — Replace getDarkMode() with CSS tokens

For each of the 10 files calling `getDarkMode()`:
1. Replace the conditional inline style with a CSS custom property reference
2. If the style is too complex for a single token, create a component-scoped
   CSS class with `.dark` override

Example migration:
```tsx
// Before
const color = getDarkMode() ? '#e1e1e1' : '#656d7b'
<span style={{ color }}>...</span>

// After
<span style={{ color: 'var(--color-text-secondary)' }}>...</span>
```

### Step 4 — Remove getDarkMode() export

Once all call sites are migrated, remove `getDarkMode()` from `darkMode.ts`.
Keep only `setDarkMode()` for the toggle switch.

### Step 5 — Validate with Storybook

Add a dark mode decorator to Storybook that toggles the `.dark` class on the
preview body. Verify every existing story renders correctly in both themes.

## Acceptance Criteria

- [ ] Every SCSS file that defines colour/background/border values has a
      corresponding `.dark` override
- [ ] Zero `getDarkMode()` calls remain in component code (only `setDarkMode()`
      in `DarkModeSwitch.tsx` and `darkMode.ts`)
- [ ] Toast, buttons (tertiary/danger/transparent), and form inputs all have
      complete dark mode styles
- [ ] `data-bs-theme` attribute is only used for Bootstrap variable overrides,
      not in custom SCSS selectors
- [ ] No hardcoded light-only colours (`#1A2634`, `white`, `#777`) appear without
      a `.dark` counterpart
- [ ] `npm run build` passes; no visual regressions in light mode
- [ ] Storybook dark mode decorator works for all existing stories

## Dependencies

- **LR-6** (Colour primitives) and **LR-2** (Semantic tokens) should be completed
  first — dark overrides are much simpler when tokens exist
- **QW-1** (Icon currentColor fix) should be applied first — it resolves the icon
  portion of dark mode independently
- Enables better accessibility scores — several WCAG AA contrast failures are
  dark-mode-specific

---
Part of the Design System Audit (#6606)
