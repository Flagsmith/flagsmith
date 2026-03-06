---
title: "Introduce semantic colour tokens (CSS custom properties)"
labels: ["design-system", "large-refactor", "dark-mode", "colours"]
---

## Problem

Dark mode is implemented via three parallel mechanisms that do not compose:

1. **SCSS `.dark` selectors** (48 rules across 29 files) — compile-time only, cannot be used in inline styles
2. **`getDarkMode()` runtime calls** (13 components) — manual ternaries that are easy to forget or get wrong
3. **Bootstrap `data-bs-theme`** — set on the root element but underused; conflicts with `.dark` selectors in places

The `$component-property-dark` SCSS variable suffix convention requires every value to be duplicated. There is no single source of truth for what a colour means in each theme.

## Files

- `web/styles/_variables.scss` — 48 `.dark` override rules
- `common/utils/colour.ts` (or equivalent) — `getDarkMode()` used in 13 components
- All 13 components calling `getDarkMode()` — manual ternary colour logic

## Proposed Fix

Introduce CSS custom properties as the single source of truth:

- `common/theme/tokens.ts` — token definitions importable in TypeScript (`import { colorTextStandard } from 'common/theme'`)
- `web/styles/_tokens.scss` — token declarations with `:root` (light values) and `[data-bs-theme='dark']` (dark overrides)

Both files are already drafted on the `chore/design-system-audit-6606` branch.

### Migration path

1. Token files already exist (drafted on audit branch) — merge and stabilise
2. Fix `Icon.tsx` with `currentColor` (QW-1)
3. Migrate all 13 `getDarkMode()` callsites to CSS custom properties
4. Migrate `.dark` SCSS selectors component-by-component
5. Remove orphaned `$*-dark` SCSS variables once all callsites are migrated

## Acceptance Criteria

- [ ] `common/theme/tokens.ts` is merged and exported
- [ ] `web/styles/_tokens.scss` defines all semantic tokens under `:root` and `[data-bs-theme='dark']`
- [ ] All 13 `getDarkMode()` callsites are removed
- [ ] All 48 `.dark` SCSS override rules are replaced with token usage
- [ ] Orphaned `$*-dark` variables are deleted
- [ ] Light and dark mode render correctly across all migrated components

## Storybook Validation

- `Design System/Colours/Semantic Tokens` — verify token values in both themes
- `Design System/Dark Mode Issues/Theme Token Comparison` — side-by-side light/dark comparison

## Dependencies

LR-6 (formal colour palette must be defined before semantic tokens can reference it meaningfully)

---
Part of the Design System Audit (#6606)
