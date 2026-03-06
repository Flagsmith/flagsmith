# Design System — Actionable Issues

**Related**: Issue #6606, `DESIGN_SYSTEM_AUDIT.md` (on `chore/design-system-audit-6606` branch), PR #6105 (Tailwind POC — not yet adopted)
**Date**: 2026-03-05
**Storybook validation**: Run `npm run storybook` to see issues visually. Available stories:
- **Design System/Icons** — All Icons, Dark Mode Broken, Hardcoded Fills, Semantic Defaults, Separate SVG Components, Icon System Summary
- **Design System/Colours** — Semantic Tokens, Current SCSS Variables
- **Design System/Colours/Palette Audit** — Tonal Scale Inconsistency, Alpha Colour Mismatches, Orphan Hex Values, Grey Scale Gaps
- **Design System/Buttons** — All Variants, Dark Mode Gaps, Size Variants
- **Design System/Dark Mode Issues** — Hardcoded Colours In Components, Dark Mode Implementation Patterns, Theme Token Comparison
- **Design System/Typography** — Type Scale, Hardcoded Font Sizes, Proposed Tokens

Each finding below is a potential GitHub issue. Grouped by size: quick wins first, then medium efforts, then large refactors.

---

## Quick Wins (1–2 hours each)

### QW-1: Icon.tsx — Replace `#1A2634` defaults with `currentColor`

**Problem**: ~54 SVG icons in `Icon.tsx` default their `fill` to `#1A2634` (dark navy). This colour is invisible on dark mode backgrounds (`$body-bg-dark: #101628`).

**Files**:
- `web/components/Icon.tsx` — 46 instances of `fill={fill || '#1A2634'}`, plus `stroke: fill || '#1a2634'` in 3 diff icon paths

**Affected icons**: checkmark, chevron-down, chevron-left, chevron-right, chevron-up, arrow-left, arrow-right, clock, code, copy, copy-outlined, dash, diff, edit, edit-outlined, email, file-text, flash, flask, height, bell, calendar, layout, layers, list, lock, minus-circle, more-vertical, people, person, pie-chart, refresh, request, setting, settings-2, shield, star, timer, trash-2, bar-chart, award, options-2, open-external-link, features, rocket, expand, radio, and more.

**Fix**: Replace all `fill={fill || '#1A2634'}` with `fill={fill || 'currentColor'}`. This inherits the text colour from the parent element, working in both light and dark mode automatically.

**Impact**: Fixes ~54 broken icons in dark mode in one go. Highest ROI fix in the entire audit.

**Validate**: Storybook → "Design System/Icons/Dark Mode Broken" (toggle dark mode in toolbar).

---

### QW-2: Hardcoded `#1A2634` in components outside Icon.tsx

**Problem**: Several components pass `#1A2634` directly to icons or chart elements.

**Files & lines**:
| File | Line | Code |
|------|------|------|
| `web/components/StatItem.tsx` | 43 | `fill='#1A2634'` |
| `web/components/Switch.tsx` | 57 | `fill={checked ? '#656D7B' : '#1A2634'}` |
| `web/components/DateSelect.tsx` | 136 | `fill={isOpen ? '#1A2634' : '#9DA4AE'}` |
| `web/components/pages/ScheduledChangesPage.tsx` | 126 | `fill={'#1A2634'}` |
| `web/components/organisation-settings/usage/OrganisationUsage.container.tsx` | 63 | `tick={{ fill: '#1A2634' }}` |
| `web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx` | 62 | `tick={{ fill: '#1A2634' }}` |

**Fix**: After QW-1, stop passing `fill` entirely (icons will use `currentColor`). For chart ticks, import `colorTextStandard` from `common/theme` and use it directly.

**Already correct**: `CompareIdentities.tsx:214` and `RuleConditionValueInput.tsx:150` use `getDarkMode()` conditionals.

**Validate**: Storybook → "Design System/Dark Mode Issues/Hardcoded Colours In Components".

---

### QW-3: Chart axis labels invisible in dark mode

**Problem**: Recharts `<XAxis>` and `<YAxis>` components use hardcoded tick fill colours.

**Files**:
- `web/components/organisation-settings/usage/OrganisationUsage.container.tsx` lines 56, 63
- `web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx` lines 53, 62
- `web/components/pages/admin-dashboard/components/UsageTrendsChart.tsx`
- `web/components/feature-page/FeatureNavTab/FeatureAnalytics.tsx`

**Fix**: Import `colorTextStandard` and `colorTextSecondary` from `common/theme` and use them for tick fills. This automatically adapts to light/dark mode.

---

### QW-4: Release pipeline hardcoded colours

**Problem**: Release pipeline status indicators use raw hex values instead of theme variables.

**Files**:
- `web/components/release-pipelines/ReleasePipelinesList.tsx:169` — `color: isPublished ? '#6837FC' : '#9DA4AE'`
- `web/components/release-pipelines/ReleasePipelineDetail.tsx:106` — same pattern
- `web/components/release-pipelines/StageCard.tsx:8` — `bg-white` hardcoded, no dark mode

**Fix**: Use tokens from `common/theme` — `colorBrandPrimary` and `colorTextTertiary`.

---

### QW-5: Remove unused `ionicons` dependency

**Problem**: `ionicons` (v7.2.1) and `@ionic/react` (v7.5.3) are installed in `package.json` but not used anywhere in the codebase.

**Fix**: `npm uninstall ionicons @ionic/react`. Saves bundle size and removes a confusing dependency.

---

### QW-6: Fix 9 icons with hardcoded fills that ignore the `fill` prop

**Problem**: 9 icons have fills baked directly into SVG path elements, making the `fill` prop useless:

| Icon | Colour | Issue |
|------|--------|-------|
| `github` | `#1A2634` | Invisible in dark mode |
| `pr-draft` | `#1A2634` | Invisible in dark mode |
| `google` | Multi-colour brand | Intentional — keep as-is |
| `link` | `rgb(104, 55, 252)` | Should use `$primary` / `currentColor` |
| `pr-merged` | `#8957e5` | GitHub purple — intentional? |
| `issue-closed` | `#8957e5` | Same |
| `issue-linked` | `#238636` | GitHub green — intentional? |
| `pr-linked` | `#238636` | Same |
| `pr-closed` | `#da3633` | GitHub red — intentional? |

**Fix**: For `github` and `pr-draft`, switch to `fill={fill || 'currentColor'}`. For GitHub status icons, decide: use `currentColor` (adapts to theme) or keep brand colours (intentional). For `link`, use `currentColor`.

**Validate**: Storybook → "Design System/Icons/Hardcoded Fills".

---

### QW-7: Wire accessibility E2E tests into CI

**Problem**: 6 axe-core/Playwright E2E tests already exist (`e2e/tests/accessibility-tests.pw.ts`) covering WCAG 2.1 AA compliance — light/dark contrast on Features page, Project Settings, Environment Switcher, and Create Feature modal. But they aren't wired into the CI pipeline, so contrast regressions can ship undetected.

**Files**:
- `e2e/tests/accessibility-tests.pw.ts` — existing tests
- `e2e/helpers/accessibility.playwright.ts` — `checkA11y()` helper
- CI config (GitHub Actions workflow) — needs accessibility test job

**Fix**: Add the accessibility tests to the existing Playwright CI job. Tests only fail on critical/serious violations, so they won't be noisy.

**Impact**: Prevents contrast regressions from shipping. Zero new code needed — just CI config.

---

### QW-8: Fix invalid `fontWeight: 'semi-bold'` in SuccessMessage

**Problem**: `SuccessMessage.tsx` and `SuccessMessage.js` both use `fontWeight: 'semi-bold'` — this is not a valid CSS value. The browser ignores it entirely, so the text renders at the inherited weight instead of semi-bold.

**Files**:
- `web/components/messages/SuccessMessage.tsx`
- `web/components/SuccessMessage.js`

**Fix**: Replace `'semi-bold'` with `600` (the numeric value for semi-bold).

---

## Medium Efforts (half-day to 1 day each)

### ME-1: Consolidate 6 identical `ConfirmRemove*` modals

**Problem**: Six deletion confirmation modals follow the exact same "type the name to confirm" pattern with nearly identical code:

- `modals/ConfirmRemoveFeature.tsx`
- `modals/ConfirmRemoveSegment.tsx`
- `modals/ConfirmRemoveProject.tsx`
- `modals/ConfirmRemoveOrganisation.tsx`
- `modals/ConfirmRemoveEnvironment.tsx`
- `modals/ConfirmRemoveWebhook.tsx`

**Fix**: Create a single `ConfirmRemoveModal` component that takes `entityType`, `entityName`, and `onConfirm` props. Replace all 6 files with imports of the shared component.

**Impact**: Removes ~500 lines of duplicated code.

---

### ME-2: Button variant dark mode gaps

**Problem**: `btn-tertiary`, `btn-danger`, and `btn--transparent` have no dark mode overrides despite variables being defined (`$btn-tertiary-bg-dark`, etc.).

**Files**:
- `web/styles/project/_buttons.scss` — needs `.dark` overrides for missing variants
- Variables already exist in `_variables.scss` lines 137–144

**Fix**: Add `.dark` selectors in `_buttons.scss` that use the existing dark mode variables. Test all button variants in both themes.

**Validate**: Storybook → "Design System/Buttons/Dark Mode Gaps" (toggle dark mode in toolbar).

---

### ME-3: Convert `Input.js` to TypeScript

**Problem**: The main form input component `web/components/base/forms/Input.js` is a legacy class component (231 lines) that hasn't been converted to TypeScript. It handles text inputs, passwords, search, checkboxes, and radio buttons in one component.

**Fix**: Convert to TypeScript functional component. Consider splitting password toggle and search input into separate variants via props rather than internal branching.

---

### ME-4: Toast notifications — add dark mode support

**Problem**: Toast notifications (`web/project/toast.tsx`) have no dark mode styles. The inline SVGs for success/danger icons use hardcoded colours.

**Fix**: Add `.dark .toast-message` CSS overrides. Replace hardcoded SVGs with the `Icon` component (after QW-1 is done).

---

### ME-5: Unify dropdown implementations

**Problem**: 4 different dropdown patterns exist:
1. `base/DropdownMenu.tsx` — icon-triggered action menu
2. `base/forms/ButtonDropdown.tsx` — split button dropdown
3. `navigation/AccountDropdown.tsx` — account menu (duplicates DropdownMenu positioning logic)
4. `segments/Rule/components/EnvironmentSelectDropdown.tsx` — form-integrated dropdown

**Fix**: Standardise on `DropdownMenu` for action menus. Refactor `AccountDropdown` to use `DropdownMenu` as its base. Document when to use `ButtonDropdown` vs `DropdownMenu`.

---

### ME-6: Checkbox and switch dark mode states

**Problem**: `Switch.tsx` uses hardcoded colours for sun/moon icons. Form checkboxes/radio buttons in `Input.js` have no dark mode overrides for their custom styles.

**Fix**: Use CSS variables or `currentColor` for Switch icons. Add `.dark` overrides for checkbox/radio custom styles in SCSS.

---

### ME-7: Consolidate 23 separate SVG icon components

**Problem**: 23 SVG icon components exist outside of `Icon.tsx` across 3 directories:
- `web/components/svg/` — 19 navigation/sidebar icons (AuditLogIcon, FeaturesIcon, SegmentsIcon, etc.)
- `web/components/base/icons/` — 2 icons (GithubIcon, GitlabIcon)
- `web/components/` — 2 icons (IdentityOverridesIcon, SegmentOverridesIcon)

These are imported directly by components, bypassing the `<Icon name="..." />` API. There is no shared pattern for props, sizing, or colour handling.

**Fix**: Either:
1. Add these to the `Icon.tsx` switch statement so all icons use one API, or
2. Extract `Icon.tsx`'s inline SVGs into individual files (part of LR-1) and merge all icons into the same structure.

Option 2 is better long-term. Short-term, document which components import which icons.

**Validate**: Storybook → "Design System/Icons/Separate SVG Components".

---

### ME-8: Add `@storybook/addon-a11y` for component-level contrast checks

**Problem**: Storybook is set up with visual stories for icons, buttons, colours, and dark mode issues, but has no automated accessibility checking. Developers can only spot contrast issues by eye.

**Fix**: Install `@storybook/addon-a11y` and add to `.storybook/main.ts`. Every story automatically gets a WCAG 2.1 AA accessibility panel showing contrast failures, missing ARIA attributes, and keyboard issues — at component level, not page level.

**Impact**: Complements the existing E2E axe-core tests (page-level) with a faster component-level feedback loop. Developers see violations while building, not after deployment.

**Validate**: Storybook → any story → "Accessibility" tab in addon panel.

---

### ME-9: Expand accessibility E2E coverage to all key pages

**Problem**: The 6 existing axe-core tests only cover: Features page (light + dark), Project Settings, Environment Switcher, Create Feature modal. Many pages have no automated accessibility coverage at all.

**Missing pages**: Segments, Audit Log, Integrations, Users & Permissions, Organisation Settings, Identities, Release Pipelines, Change Requests.

**Fix**: Add light and dark mode contrast tests for each missing page, following the existing pattern in `e2e/tests/accessibility-tests.pw.ts`. Focus on critical/serious violations only.

**Impact**: Catches contrast and ARIA issues across the full app surface area, not just a handful of pages.

---

### ME-10: Typography inconsistencies — enforce the existing type scale

**Problem**: An h1–h6 scale and body size variables exist in SCSS, but they're widely bypassed:

**Font sizes** — 58 hardcoded inline `fontSize` values in TSX:

| Value | Occurrences | Where |
|-------|-------------|-------|
| `fontSize: 13` | 17 | Admin dashboard, tables, various components |
| `fontSize: 12` | 12 | Labels, captions, badges |
| `fontSize: 11` | 7 | Table filters, small labels |
| `fontSize: 10` | 1 | Icon labels |
| Other (`14px`, `16px`, `18px`, `0.875rem`) | ~6 | Scattered |

**Font weights** — 4 tiers are used in practice (700, 600, 500, 400) but applied inconsistently:
- Mixed systems: custom `.font-weight-medium` (500) alongside Bootstrap `fw-bold`/`fw-semibold`/`fw-normal`
- 9 inline `fontWeight` values in TSX bypassing classes entirely
- `fontWeight: 'semi-bold'` in `SuccessMessage.tsx` and `SuccessMessage.js` — **invalid CSS** (should be 600)

**"Subtle" text** — achieved via opacity (0.4–0.75) rather than colour tokens, which is an accessibility concern for low-vision users. Classes `.faint`, `.text-muted` exist but compete with ad-hoc opacity values.

**Utility classes** — minimal and inconsistent. Only `.text-small`, `.large-para`, `.font-weight-medium`, `.bold-link`. No systematic set.

**Fix**:
1. Replace the 58 hardcoded `fontSize` values with existing SCSS variables or CSS classes
2. Standardise on one weight class system (either custom or Bootstrap, not both)
3. Replace opacity-based muted text with colour-based approach (`$text-muted` / `colorTextSecondary`)
4. Fix the `semi-bold` bug in SuccessMessage

**Validate**: Storybook → "Design System/Typography".

---

## Large Refactors (multi-day)

### LR-1: Icon.tsx — break up monolithic component

**Problem**: `Icon.tsx` is 1,543 lines containing 70+ inline SVG definitions in a single switch statement. It's the single largest component in the codebase. Adding, modifying, or debugging icons requires navigating this massive file.

One icon (`paste`) is declared in the `IconName` type but has no implementation.

**Fix**: Extract each icon into its own file under `web/components/icons/`. Create an `IconMap` that lazy-loads icons by name. Keep the `<Icon name="..." />` API but back it with individual files.

**Prerequisite**: QW-1 (fix `currentColor` defaults first).

---

### LR-2: Introduce semantic colour tokens (CSS custom properties)

**Problem**: Dark mode is implemented via 3 parallel mechanisms that don't compose:
1. **SCSS `.dark` selectors** (48 rules across 29 files) — compile-time, can't be used in inline styles
2. **`getDarkMode()` runtime calls** (13 components) — manual ternaries, easy to forget
3. **Bootstrap `data-bs-theme`** — set but underused, conflicts with manual `.dark` selectors

Variables use a `$component-property-dark` suffix convention (`$input-bg-dark`, `$panel-bg-dark`, etc.) requiring duplicate SCSS rules for every property.

**Fix**: Introduce CSS custom properties via `common/theme/tokens.ts` + `web/styles/_tokens.scss` (already drafted on this branch). These tokens:
- Define light values on `:root` and dark values on `[data-bs-theme='dark']`
- Are importable in TS files: `import { colorTextStandard } from 'common/theme'`
- Eliminate `getDarkMode()` calls entirely
- Gradually replace `.dark` selector pairs

**Migration path**:
1. Token files already exist (drafted)
2. Fix Icon.tsx with `currentColor` (QW-1) — no tokens needed
3. Migrate `getDarkMode()` callsites (13 files) to use token imports
4. Migrate `.dark` selectors component-by-component
5. Remove orphaned `$*-dark` SCSS variables

**Validate**: Storybook → "Design System/Colours/Semantic Tokens" (toggle dark mode to see tokens flip). Also see "Design System/Dark Mode Issues/Theme Token Comparison" for before/after code examples.

---

### LR-3: Modal system — migrate from global imperative API

**Problem**: The modal system uses `openModal()`, `openModal2()`, `openConfirm()` as global functions attached to `window`. It uses deprecated `react-dom` `render`/`unmountComponentAtNode` APIs (removed in React 18). `openModal2` exists for stacking modals, acknowledged in code comments as a pattern to avoid.

**Fix**: Migrate to a React context-based modal manager. Replace global imperative calls with `useModal()` hook. This is a large effort but unblocks React 18 compatibility.

---

### LR-4: Standardise table/list components

**Problem**: No unified table/list component system. Each feature area builds its own:
- 9 different `TableFilter*` components
- 5+ different `*Row` components (FeatureRow, ProjectFeatureRow, FeatureOverrideRow, OrganisationUsersTableRow, etc.)
- 5+ different `*List` components

**Fix**: Create a composable `<Table>` / `<List>` component system with standardised `Row`, `Cell`, and `Header` sub-components. Migrate feature areas one at a time.

---

### LR-5: Remove legacy JS class components

**Problem**: Several components remain as `.js` class components:
- `base/forms/Input.js`
- `base/forms/InputGroup.js`
- `modals/CreateProject.js`
- `modals/CreateWebhook.js` (coexists with `.tsx` version)
- `modals/Payment.js`
- Layout: `Flex.js`, `Column.js`

**Fix**: Convert each to TypeScript functional components. Remove `CreateWebhook.js` duplicate.

---

### LR-6: Define a formal colour palette

**Problem**: There is no formal, systematic colour palette. The current state:

1. **Inconsistent tonal scales**: `$primary400` (`#956CFF`) is *lighter* than `$primary` (`#6837FC`), reversing the typical convention where higher numbers = darker. `$bg-dark500` is darker than `$bg-dark100`, but text/grey scales don't follow a pattern at all.

2. **Alpha colour RGB mismatches**: The alpha variants use different base RGB values than their solid counterparts:
   | Token | Solid hex | Solid RGB | Alpha base RGB |
   |-------|-----------|-----------|----------------|
   | `$primary` / `$primary-alfa-*` | `#6837FC` | `(104, 55, 252)` | `(149, 108, 255)` |
   | `$danger` / `$danger-alfa-*` | `#EF4D56` | `(239, 77, 86)` | `(255, 66, 75)` |
   | `$warning` / `$warning-alfa-*` | `#FF9F43` | `(255, 159, 67)` | `(255, 159, 0)` |

3. **30+ orphan hex values in components**: Colours used directly in TSX/SCSS that don't exist in `_variables.scss`:
   - `#9DA4AE` (52 uses) — a grey with no variable
   - `#656D7B` (44 uses) — has variable `$text-icon-grey` but most callsites use raw hex
   - `#e74c3c`, `#53af41`, `#767d85`, `#5D6D7E`, `#343a40`, `#1c2840`, `#8957e5`, `#238636`, `#da3633` etc.

4. **Missing scale steps**: No `$danger600`, no `$success700`, no `$info400`, no `$warning200`. Each colour has a different number of tonal variants, making the system unpredictable.

5. **No grey scale**: Greys are named ad hoc (`$text-icon-grey`, `$text-icon-light-grey`, `$bg-light200`, `$footer-grey`) with no numbered scale.

**Fix**: Define a formal primitive palette with consistent naming:
- Numbered tonal scales (50–900) for each hue, following the convention: lower numbers = lighter
- Derive alpha variants from the same RGB as the solid colour
- Create a proper grey/neutral scale
- Map every orphan hex to a palette token or remove it

**Impact**: This is the prerequisite for semantic tokenisation (LR-2). Without a consistent palette, tokens just paper over the mess.

**Note**: PR #6105 is a Tailwind CSS POC (not yet adopted). If Tailwind is adopted, `theme.extend.colors` could be the home for the palette definition, generating CSS custom properties consumed by both utility classes and the semantic token layer. The palette work itself is Tailwind-agnostic — it needs doing regardless.

**Validate**: Storybook → "Design System/Colours/Palette Audit" — four stories covering tonal scale inconsistency, alpha mismatches, orphan hex values, and grey scale gaps.

---

### LR-7: Full dark mode theme audit (umbrella)

**Problem**: Only 48 `.dark` CSS selectors exist across the entire stylesheet. Many component areas have zero dark mode coverage:
- Feature pipeline visualisation (white circles, grey lines on dark background)
- Admin dashboard charts
- Integration cards
- Numerous inline styles with light-mode-only colours

**Fix**: Systematic page-by-page dark mode audit. For each page:
1. Toggle dark mode
2. Screenshot
3. Identify contrast failures
4. Add `.dark` overrides or switch to `currentColor` / CSS variables

This is the umbrella issue — all the QW and ME items above contribute to this.

**Validate**: Storybook → "Design System/Dark Mode Issues/Dark Mode Implementation Patterns" — shows all 3 parallel mechanisms and the proposed solution.

---

### LR-8: Standardise typography usage across the codebase

**Problem**: The type scale (h1–h6, body sizes, weight tiers) exists in SCSS but is bypassed in 58+ places with inline styles. The weight system is fragmented between custom classes (`.font-weight-medium`) and Bootstrap utilities (`fw-bold`, `fw-semibold`). "Subtle" text uses opacity instead of semantic colour. Without enforcing the existing scale, inconsistencies will keep growing.

**Fix**:
1. Replace all 58 inline `fontSize` values with existing SCSS variables or utility classes
2. Pick one weight class system and migrate the other (e.g. standardise on Bootstrap `fw-*` and remove `.font-weight-medium`, or vice versa)
3. Replace opacity-based muted text patterns with `$text-muted` / `colorTextSecondary`
4. Optionally introduce a `<Text>` component if the migration shows repeated patterns that would benefit from a constrained API — but only if the need is demonstrated, not upfront

**Prerequisite**: ME-10 (audit and consolidate the type scale first).

---

## Summary

| Category | Count | Estimated total effort |
|----------|-------|----------------------|
| Quick wins | 8 | 1–2 days |
| Medium efforts | 10 | 5–10 days |
| Large refactors | 8 | 4–7 weeks |

**Recommended order**: QW-1 → QW-5 → QW-6 → QW-7 → QW-2 → QW-3 → ME-8 → ME-2 → ME-4 → ME-10 → ME-9 → ME-7 → ME-1 → LR-1 → LR-6 → LR-2 → LR-8 → rest.

**Key dependency chains**:
- QW-1 (icon currentColor) → QW-2 (component hardcoded colours) → LR-1 (break up Icon.tsx)
- LR-6 (formal palette) → LR-2 (semantic tokens)
- ME-10 (typography tokens) → LR-8 (Text/Heading components)
- QW-7 (CI a11y tests) → ME-9 (expand a11y coverage)

---

## Appendix: Icon System Inventory

| Category | Count | Details |
|----------|-------|---------|
| Icons in `Icon.tsx` switch | 70 | All inline SVGs, 1,543 lines |
| Icons declared but not implemented | 1 | `paste` — in type, no case |
| Separate SVG components | 23 | Across `svg/`, `base/icons/`, root |
| Integration SVG files | 37 | In `/static/images/integrations/` |
| Icons defaulting to `#1A2634` | ~54 | Invisible in dark mode |
| Icons with hardcoded fills | 9 | Cannot be overridden via props |
| Icons using `currentColor` | 0 | None |
| Unused icon dependency | `ionicons` v7.2.1 | Installed but never imported |
