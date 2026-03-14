# Frontend Design System Audit — Findings Report

**Epic**: [#6882 — Resolve UI inconsistencies and consolidation](https://github.com/Flagsmith/flagsmith/issues/6882)
**Parent issue**: [#6606 — Audit frontend UI](https://github.com/Flagsmith/flagsmith/issues/6606)
**Branch**: `chore/design-system-audit-6606`
**Date**: 2026-03-09

### Related epics

- [#5746 — Modernize UI Codebase With TS and FS components](https://github.com/Flagsmith/flagsmith/issues/5746) — JS → TS migration effort. Overlaps with NP-5 (TypeScript-first) and ME-3 (Input.js). `Payment.js` migration already tracked as [#6319](https://github.com/Flagsmith/flagsmith/issues/6319).
- [#5921 — Platform UI improvements, fixes and responsiveness](https://github.com/Flagsmith/flagsmith/issues/5921) — UI bug backlog. [#6414](https://github.com/Flagsmith/flagsmith/issues/6414) (inconsistent header font colour) overlaps with ME-10 / NP-8 (typography).
- [PR #6764 — React 19 migration](https://github.com/Flagsmith/flagsmith/pull/6764) — Handles `ReactDOM.render` removal in modal system and `main.js`. Resolves the React compat concern in NP-3.

## Storybook evidence

Run `npm run storybook` on this branch to see visual evidence for each finding:

- **Design System/Icons** — All Icons, Dark Mode Broken, Hardcoded Fills, Semantic Defaults, Separate SVG Components
- **Design System/Colours** — Semantic Tokens, Current SCSS Variables
- **Design System/Colours/Palette Audit** — Tonal Scale Inconsistency, Alpha Colour Mismatches, Orphan Hex Values, Grey Scale Gaps
- **Design System/Buttons** — All Variants, Dark Mode Gaps, Size Variants
- **Design System/Dark Mode Issues** — Hardcoded Colours In Components, Implementation Patterns, Theme Token Comparison
- **Design System/Typography** — Type Scale, Hardcoded Font Sizes, Proposed Tokens

---

## Quick Wins — GitHub Issues Created

These are small, well-scoped fixes (1–2 hours each). All are sub-issues of epic #6882.

| ID | Title | GitHub | Status |
|----|-------|--------|--------|
| QW-1 | Replace hardcoded icon fill with `currentColor` | [#6869](https://github.com/Flagsmith/flagsmith/issues/6869) / [PR #6870](https://github.com/Flagsmith/flagsmith/pull/6870) | In review |
| QW-3 | Chart axis colours invisible in dark mode | [#6889](https://github.com/Flagsmith/flagsmith/issues/6889) | Open |
| QW-7 | POC: Evaluate wiring a11y E2E tests into CI | [#6890](https://github.com/Flagsmith/flagsmith/issues/6890) | Open |
| QW-8 | Fix invalid `fontWeight: 'semi-bold'` in SuccessMessage | [#6872](https://github.com/Flagsmith/flagsmith/issues/6872) / [PR #6873](https://github.com/Flagsmith/flagsmith/pull/6873) | In review |
| QW-9 | Fix SidebarLink hover state broken in dark mode | [#6868](https://github.com/Flagsmith/flagsmith/issues/6868) / [PR #6871](https://github.com/Flagsmith/flagsmith/pull/6871) | In review |
| QW-10 | Decouple Button from Redux store (dead feature prop) | [#6866](https://github.com/Flagsmith/flagsmith/issues/6866) | Open |
| QW-11 | Remove legacy ErrorMessage.js, consolidate imports | [#6891](https://github.com/Flagsmith/flagsmith/issues/6891) | Open |
| QW-12 | Button dark mode gaps (btn-tertiary, btn-danger, btn--transparent) | [#6892](https://github.com/Flagsmith/flagsmith/issues/6892) | Open |
| QW-13 | Toast notifications: add dark mode support | [#6893](https://github.com/Flagsmith/flagsmith/issues/6893) | Open |
| QW-14 | Checkbox and switch dark mode states | [#6894](https://github.com/Flagsmith/flagsmith/issues/6894) | Open |

### Reclassified / absorbed

| Original ID | What happened |
|--------------|---------------|
| QW-2 | Absorbed into QW-1 — PR #6870 expanded scope to cover all hardcoded fills |
| QW-4 | Reclassified to ME — 19 hex values across 8 files, not a quick win |
| QW-5 (ionicons) | Absorbed into LR-1 — 40+ files import IonIcon, cannot simply uninstall |
| QW-6 | Absorbed into QW-1 — PR #6870 also fixed icons with hardcoded SVG fills |

---

## Medium Efforts — Documented for Evaluation

These are half-day to 1-day tasks. Not yet created as GitHub issues — to be evaluated and prioritised by the team.

### ~~ME-1~~ → Absorbed into NP-3 (Context-based modal system)

Consolidating the 6 identical ConfirmRemove modals is the first step of introducing the new modal pattern — no point doing it separately.

### ~~ME-3~~ → Reclassified as NP-10 (Form building blocks)

### ~~ME-4~~ → First sub-task of NP-7 (Fix dark mode gaps)

Release pipeline: 19 raw hex values across 8 files (`#6837FC`, `#9DA4AE`, `#656D7B`, `bg-white`). Good candidate for the first page-by-page token adoption after NP-2 lands.

### ME-5: Unify dropdown implementations *(nice to have — no ticket)*

4 competing dropdown patterns with no clear guidance:

1. `base/DropdownMenu.tsx` — canonical action menu
2. `base/forms/ButtonDropdown.tsx` — split button
3. `navigation/AccountDropdown.tsx` — duplicates DropdownMenu positioning logic
4. `segments/Rule/components/EnvironmentSelectDropdown.tsx` — form-integrated

Not breaking anything — just inconsistent. If touched during other work, consider standardising on `DropdownMenu` as base.

### ~~ME-9~~ → Will come as a result of QW-7 (a11y POC)

Expanding a11y E2E coverage to all key pages (Segments, Audit Log, Integrations, etc.) depends on the QW-7 POC outcome. If the POC recommends wiring tests into CI, the scope and ticket will follow from that.

### ~~ME-10~~ → Absorbed into NP-8 (Typography tokens)

The 58 hardcoded `fontSize` values and competing weight systems are the migration work of NP-8 — same pattern as NP-7/NP-2. No separate ticket needed.

**See also**: [#6414](https://github.com/Flagsmith/flagsmith/issues/6414) (inconsistent header font colour) under [#5921](https://github.com/Flagsmith/flagsmith/issues/5921).

### ~~ME-11~~ → Deferred to Tailwind adoption

Off-grid values (`5px`, `6px`, `3px`, `15px`, `19px`) need a spacing scale — but Tailwind ships one out of the box (`p-1` = 4px, `p-2` = 8px, etc.). No point building custom spacing tokens if Tailwind is coming. Clean up hardcoded values with utility classes when Tailwind lands.

### ME-8: @storybook/addon-a11y ✅ Done

Already installed on this branch. Every story has a WCAG 2.1 AA "Accessibility" panel.

---

## New Patterns — Documented for Evaluation

These introduce new patterns to follow going forward. The key principle: **introduce the pattern once, then migrate incrementally** as you touch files during normal feature work and bug fixes. No big-bang refactors needed.

### NP-1: Unified icon system

**Current state**: `Icon.tsx` is 1,543 lines with 70+ inline SVGs in a single switch. Three icon systems coexist: `Icon.tsx` (60+ icons), `web/components/svg/` (19 components), and IonIcon (40+ files). No tree-shaking possible.

**New pattern**: Individual icon files under `web/components/icons/`, each exporting a component that defaults to `fill="currentColor"`. Barrel export with `IconName` type.

**Adoption strategy**:
1. Create the `icons/` directory structure and barrel export
2. New icons always go in `icons/`
3. When touching a file that uses `Icon.tsx` or IonIcon, migrate that usage
4. IonIcon references shrink naturally as files are touched

**Absorbs**: QW-5 (ionicons), ME-7 (SVG consolidation)
**After**: QW-1 (currentColor defaults first)

### NP-2: Semantic colour tokens (CSS custom properties) 🔄 In progress

**Current state**: Dark mode via 3 parallel mechanisms — `.dark` SCSS selectors (48 rules, 29 files), `getDarkMode()` runtime calls (13 components), `data-bs-theme` (underused).

**New pattern**: CSS custom properties as the single source of truth — `:root` for light, `[data-bs-theme='dark']` for dark. Importable in TS: `import { colorTextStandard } from 'common/theme'`.

**Adoption strategy**:
1. Ship `_tokens.scss` + `tokens.ts` (already drafted on `chore/design-system-tokens`)
2. New/modified code uses tokens instead of hardcoded values or `getDarkMode()`
3. Existing `.dark` selectors and `getDarkMode()` calls are replaced when files are touched
4. No dedicated migration sprint — it happens naturally

**After**: NP-6 (colour primitives) should land first.

### NP-3: Context-based modal system

**Current state**: `openModal()`, `openModal2()`, `openConfirm()` as globals on `window`. 14 near-identical confirmation modals, 46+ call sites.

> **Note**: The deprecated `ReactDOM.render`/`unmountComponentAtNode` usage in the modal system is being resolved in [PR #6764](https://github.com/Flagsmith/flagsmith/pull/6764) (React 19 migration by Wadii). That PR handles the React compatibility issue directly. This pattern is about improving the modal API and reducing duplication — not about unblocking React 19.

**New pattern**: `ModalProvider` context with `useModal()` hook. Single `ConfirmModal` component replacing the 14 confirmation variants (~500 lines of duplication).

**Adoption strategy**:
1. Build `ModalProvider` and mount at app root (coexists with old system)
2. Build `ConfirmModal` as the first component — consolidates the 6 `ConfirmRemove*` modals (absorbs ME-1)
3. New modals use `useModal()`
4. When modifying an existing modal, migrate it to the new system
5. Old `openModal`/`openModal2` calls shrink over time

### NP-4: Composable table/list components *(flagged for future — no ticket)*

**Current state**: No unified system — 9 `TableFilter*` components, 5+ `*Row` components, 5+ `*List` components. Each feature area builds its own.

**New pattern**: Composable `<Table>`, `<Table.Header>`, `<Table.Row>`, `<Table.Cell>`, `<List>`, `<List.Item>` with shared empty state and loading skeleton slots.

Not a near-term priority. Documented here for when the team is ready to standardise table/list patterns. When started, build one reference implementation first and migrate incrementally.

### NP-5: TypeScript-first components

**Current state**: 7 components remain as `.js` class components (`Input.js`, `InputGroup.js`, `CreateProject.js`, `CreateWebhook.js`, `Payment.js`, `Flex.js`, `Column.js`).

**New pattern**: All components in TypeScript with full prop types. No new `.js` files.

**Adoption strategy**:
1. Delete `CreateWebhook.js` (`.tsx` version already exists)
2. When modifying a `.js` component, convert it to `.tsx` as part of the PR
3. Prioritise `Input.js` (ME-3) since it's a widely-used form primitive

**See also**: [#5746](https://github.com/Flagsmith/flagsmith/issues/5746) (TS migration epic) — aligns with this pattern. `Payment.js` already tracked as [#6319](https://github.com/Flagsmith/flagsmith/issues/6319).

### NP-6: Formal colour primitive palette 🔄 In progress

**Current state**: Ad hoc grey definitions, inverted tonal scales, alpha variants using different RGB than solid counterparts, 30+ orphan hex values.

**New pattern**: `_primitives.scss` with `$slate-*`, `$purple-*`, `$red-*`, `$green-*`, `$orange-*`, `$blue-*` scales following the lower-number-is-lighter convention. Already drafted on `chore/design-system-tokens`.

**Adoption strategy**:
1. Ship `_primitives.scss` with the complete scale
2. Map existing `_variables.scss` definitions to reference primitives
3. When touching a file with orphan hex values, replace with the nearest primitive
4. Enables NP-2 (semantic tokens reference primitives)

### NP-7: Fix dark mode gaps

**Current state**: Only 48 `.dark` CSS selectors across the entire stylesheet. Large areas have zero dark mode support: feature pipeline visualisation, admin dashboard charts, integration cards, and dozens of components with inline light-mode-only hex values. The QW dark mode fixes (QW-1, QW-3, QW-12, QW-13, QW-14) cover specific components but leave most of the surface area untouched.

**Work required**: After NP-2 (semantic tokens) lands, go feature-by-feature and replace hardcoded colour values with tokens:
- 48 `.dark` SCSS selector pairs → replace with token usage
- 13 `getDarkMode()` call sites → replace with token imports
- 280+ hardcoded hex values in TSX → replace with tokens
- Feature pipeline, integration cards, admin dashboard — full dark mode pass

**Adoption strategy**:
1. QW dark mode fixes land first (specific, high-impact components)
2. NP-2 (semantic tokens) lands — the replacement vocabulary exists
3. Go page by page: Features, Segments, Audit Log, Integrations, Users & Permissions, Organisation Settings, Identities, Release Pipelines, Change Requests
4. Each page becomes a sub-task — replace hardcoded values with tokens, verify in both themes

**Blocked by**: NP-2 (semantic colour tokens) — tokens must exist before we can use them

### NP-8: Typography consistency — deferred to Tailwind adoption

**Current state**: Type scale exists in SCSS but is bypassed in 58+ places (13px × 17, 12px × 12, 11px × 7). Fragmented weight system (`.font-weight-medium` vs Bootstrap `fw-*`). 9 inline `fontWeight` values. Opacity-based muted text failing WCAG contrast.

**Decision**: Don't build custom typography tokens. Tailwind ships a complete type scale (`text-xs`, `text-sm`, `text-base`, etc.) and weight utilities (`font-medium`, `font-semibold`, etc.) out of the box. Building a parallel system now means migrating twice.

**What to do now**: Avoid adding new hardcoded `fontSize`/`fontWeight` inline styles. When Tailwind lands, replace the 58 hardcoded values with utility classes.

**Exception**: Opacity-based muted text (`opacity: 0.4–0.75`) should be replaced with `colorTextSecondary` / `$text-muted` tokens now — that's a colour/accessibility concern, not typography, and is covered by NP-2.

**See also**: [#6414](https://github.com/Flagsmith/flagsmith/issues/6414) (inconsistent header font colour) under [#5921](https://github.com/Flagsmith/flagsmith/issues/5921)

### NP-9: Explicit imports (remove global component registry)

**Current state**: `project-components.js` attaches ~15 components to `window` (`Button`, `Row`, `Select`, etc.). Defeats tree-shaking, blocks TypeScript migration, invisible dependencies.

**New pattern**: Explicit imports in every file. No `window.*` globals.

**Adoption strategy**:
1. When converting a `.js` file to `.tsx` (NP-5), add explicit imports
2. After adding imports, remove that component's `window.*` assignment
3. Registry shrinks naturally as files are converted

### NP-10: Form building blocks

**Current state**: `Input.js` is a 231-line legacy class component handling text, password, search, checkbox, and radio inputs in a single file. No TypeScript types. `InputGroup.js` wraps it with label + error display. Validation is entirely manual — inline truthiness checks, no schemas, no validation library. Utils like `isValidEmail()`, `isValidURL()`, `isValidNumber()` are scattered in `utils.tsx`.

**New pattern**: Typed form primitives as separate, single-responsibility components: `TextInput`, `SearchInput`, `PasswordInput`, `Checkbox`, `Radio`. Each with built-in validation support (`required`, `pattern`, `validate` props) — no heavy library needed, just a consistent API. `Input.js` is not refactored — it's replaced gradually.

**Adoption strategy**:
1. Build the first primitives (`TextInput`, `Checkbox`) with validation API
2. New forms use the new components
3. When touching a form that uses `Input.js`, migrate that usage
4. `Input.js` shrinks naturally until it can be deleted

**See also**: [#5746](https://github.com/Flagsmith/flagsmith/issues/5746) (TS migration epic)

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Quick wins | 10 | GitHub issues created, 3 with PRs in review |
| Medium efforts | 6 (1 done) | Documented for evaluation |
| New patterns | 10 (2 in progress) | Documented for evaluation — introduce once, adopt incrementally |
| **Total** | **27** | |

### Key dependency chains

```
QW-1 (currentColor) → NP-1 (unified icon system)
NP-6 (colour primitives) → NP-2 (semantic tokens) → NP-7 (fix dark mode gaps, page by page) using tokens
NP-8 + ME-11 (typography + spacing) → deferred to Tailwind adoption
QW-7 (a11y POC) → ME-9 (expand a11y coverage)
NP-9 (explicit imports) → NP-5 (TypeScript-first components)
NP-3 (modal system) → cleaner modal API + reduced duplication (React compat handled by PR #6764)
```

### Recommended priority order

1. **Immediate** (QW with PRs): QW-1, QW-8, QW-9 — already in review
2. **Next sprint**: QW-3, QW-10, QW-11, QW-12, QW-13, QW-14
3. **Foundation patterns** (in progress): NP-6 + NP-2 (colour primitives + semantic tokens)
4. **After tokens land**: ME-4, ME-10, ME-1
5. **Introduce remaining patterns**: NP-1, NP-3, NP-4, NP-5, NP-8, NP-9 — each introduced once, then adopted progressively

---

## Appendix: Icon System Inventory

| Category | Count |
|----------|-------|
| Icons in `Icon.tsx` switch | 70 |
| Icons declared but not implemented | 1 (`paste`) |
| Separate SVG components (`svg/`, `base/icons/`) | 23 |
| Integration SVG files (`/static/images/integrations/`) | 37 |
| Files importing IonIcon | 40+ |
| Icons that defaulted to `#1A2634` (pre QW-1) | ~54 |
| Icons with hardcoded SVG fills (pre QW-1) | 9 |

## Appendix: Highest-Frequency Orphan Hex Values

| Hex | Occurrences | Files | Current variable |
|-----|-------------|-------|-----------------|
| `#656D7B` | 75 | 48 | `$text-icon-grey` (but most callsites use raw hex) |
| `#9DA4AE` | 59 | 35 | None |
| `#1A2634` | ~54 (in Icon.tsx) | 1 | `$body-color` |
| `#6837FC` | scattered | pipeline files | `$primary` |

## Appendix: Dark Mode Coverage

| Mechanism | Count | Files |
|-----------|-------|-------|
| `.dark` CSS selectors | 48 rules | 29 SCSS files |
| `getDarkMode()` runtime calls | 13 | 13 TSX files |
| `data-bs-theme` | 1 (root) | Set but underused |
| Components with zero dark mode support | Many | Toasts, pipeline viz, integration cards, admin charts |
