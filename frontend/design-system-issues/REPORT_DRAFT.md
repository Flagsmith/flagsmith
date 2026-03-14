## Audit Results

Full report and Storybook evidence available on branch `chore/design-system-audit-6606` ([`frontend/DESIGN_SYSTEM_ISSUES.md`](https://github.com/Flagsmith/flagsmith/blob/chore/design-system-audit-6606/frontend/DESIGN_SYSTEM_ISSUES.md)). Run `npm run storybook` on that branch for visual evidence.

Work is tracked under [#6882 — Resolve UI inconsistencies and consolidation](https://github.com/Flagsmith/flagsmith/issues/6882).

---

### Scope

Audited 525 component files across `web/components/`, `web/styles/`, and `common/`. Combined code scanning (SCSS variables, inline styles, dark mode selectors) with visual review in both light and dark mode. Screenshots captured in [Penpot](https://design.penpot.app/#/workspace?team-id=72ad1239-4f5c-8115-8007-a72d5b669ca5&file-id=72ad1239-4f5c-8115-8007-a72dd0aef2fe&page-id=72ad1239-4f5c-8115-8007-a72dd0aef2ff).

---

### Findings

#### Dark Mode

The most critical category. Large portions of the UI are broken or unreadable in dark mode.

- **3 parallel theming mechanisms** that don't compose: `.dark` SCSS selectors (48 rules across 29 files), `getDarkMode()` runtime calls (13 components), and `data-bs-theme` attribute (set but underused)
- **~54 icons invisible in dark mode** — `Icon.tsx` defaulted fills to `#1A2634` (near-black), which is invisible on the dark background (`#101628`). Contrast ratio ~1.1:1
- **Button variants missing dark overrides** — `btn-tertiary`, `btn-danger`, `btn--transparent` have no `.dark` selectors despite dark variables being defined
- **Toast notifications** — zero dark mode styles, hardcoded SVG icon colours
- **Checkbox and switch** — `Switch.tsx` hardcodes sun/moon icon colours, form checkboxes/radio have no `.dark` overrides
- **Chart axis labels** — Recharts components use hardcoded tick fill colours, invisible in dark mode
- **Feature pipeline, integration cards, admin dashboard** — no dark mode coverage at all
- **SidebarLink** — hover state references non-existent CSS classes, broken in dark mode

#### Colours

No formal colour system. Values are scattered and inconsistent.

- **280+ hardcoded hex values** in TSX files not tied to any token or variable
- **Highest-frequency orphan values**: `#656D7B` (75 occurrences, 48 files), `#9DA4AE` (59 occurrences, 35 files), `#1A2634` (~54 in Icon.tsx)
- **No systematic grey/neutral scale** — greys named ad hoc (`$text-icon-grey`, `$text-icon-light-grey`, `$bg-light200`, `$footer-grey`)
- **Inverted tonal scales** — `$primary400` (`#956CFF`) is lighter than `$primary` (`#6837FC`), reversing the lower-number-is-lighter convention
- **Alpha colour RGB mismatches** — `$primary-alfa-*` uses RGB `(149, 108, 255)` but `$primary` is `(104, 55, 252)`. Same mismatch for `$danger` and `$warning` alpha variants
- **Missing scale steps** — no `$danger600`, `$success700`, `$info400`, `$warning200`
- **Release pipelines** — 19 hardcoded hex values across 8 files

#### Typography

A type scale exists in SCSS but is widely bypassed.

- **58 hardcoded inline `fontSize` values** in TSX: `13px` (17×), `12px` (12×), `11px` (7×), and more
- **9 inline `fontWeight` values** bypassing the class system
- **Competing weight systems** — custom `.font-weight-medium` alongside Bootstrap `fw-bold`/`fw-semibold`/`fw-normal`
- **Invalid CSS** — `fontWeight: 'semi-bold'` in `SuccessMessage` (browsers ignore it)
- **Opacity-based muted text** — `opacity: 0.4–0.75` instead of colour tokens, fails WCAG contrast when background isn't guaranteed

See also: [#6414](https://github.com/Flagsmith/flagsmith/issues/6414) (inconsistent header font colour)

#### Spacing

- **8px base grid** defined via `$spacer` but widely broken
- **`5px`** — 10+ occurrences across buttons, panels, tags, lists, chips
- **`6px`** — 3+ files
- **`3px`** — some intentional (centring), some not
- **`15px`, `19px`** — one-offs in tabs and icons

#### Icons

Three separate icon systems with no unified API.

- **`Icon.tsx`** — 1,543 lines, 70+ inline SVGs in a single switch statement. No tree-shaking possible
- **`web/components/svg/`** — 19 standalone SVG components with their own hardcoded fills
- **IonIcon** — 40+ files import from `ionicons`/`@ionic/react`
- **1 icon declared but not implemented** — `paste` exists in the `IconName` type but has no case
- **9 icons with fills baked into SVG elements** — `fill` prop has no effect

#### Components

Duplication and inconsistency across common patterns.

- **14 near-identical confirmation modals** — each implements its own layout, buttons, and copy for the "type name to confirm" pattern
- **4 dropdown patterns** — `DropdownMenu`, `ButtonDropdown`, `AccountDropdown` (duplicates positioning logic), `EnvironmentSelectDropdown`
- **`Input.js`** — 231-line legacy class component handling text, password, search, checkbox, and radio in one file. No TypeScript types
- **`ErrorMessage.js`** — legacy class component coexists with TypeScript replacement (`messages/ErrorMessage.tsx`). 37 files import the legacy version
- **`Button`** — imports Redux store to check a `hasFeature` prop that is always true (dead code)
- **Modal system** — `openModal()`, `openModal2()`, `openConfirm()` as globals on `window`. Uses deprecated `ReactDOM.render` (being resolved in [PR #6764](https://github.com/Flagsmith/flagsmith/pull/6764))
- **Global component registry** — `project-components.js` attaches ~15 components to `window`, defeating tree-shaking and blocking TS migration

#### Accessibility

- **Secondary text fails WCAG AA** — `#656D7B` on white gives 4.48:1 (needs 4.5:1 for normal text). Worse in dark mode
- **6 axe-core E2E tests exist** but are not wired into CI — contrast regressions can ship undetected
- **Only 6 pages covered** by a11y tests — Segments, Audit Log, Integrations, Users & Permissions, Organisation Settings, Identities, Release Pipelines, and Change Requests have no coverage

---

### What's Being Addressed

**Quick wins** — 10 GitHub issues created under [#6882](https://github.com/Flagsmith/flagsmith/issues/6882):

| Issue | What |
|-------|------|
| [#6869](https://github.com/Flagsmith/flagsmith/issues/6869) | Icons: replace hardcoded fills with `currentColor` ([PR #6870](https://github.com/Flagsmith/flagsmith/pull/6870)) |
| [#6889](https://github.com/Flagsmith/flagsmith/issues/6889) | Chart axis colours in dark mode |
| [#6890](https://github.com/Flagsmith/flagsmith/issues/6890) | POC: evaluate wiring a11y tests into CI |
| [#6872](https://github.com/Flagsmith/flagsmith/issues/6872) | Fix invalid `fontWeight: 'semi-bold'` ([PR #6873](https://github.com/Flagsmith/flagsmith/pull/6873)) |
| [#6868](https://github.com/Flagsmith/flagsmith/issues/6868) | SidebarLink hover state in dark mode ([PR #6871](https://github.com/Flagsmith/flagsmith/pull/6871)) |
| [#6866](https://github.com/Flagsmith/flagsmith/issues/6866) | Decouple Button from Redux store |
| [#6891](https://github.com/Flagsmith/flagsmith/issues/6891) | Remove legacy ErrorMessage.js |
| [#6892](https://github.com/Flagsmith/flagsmith/issues/6892) | Button dark mode gaps (tertiary, danger, transparent) |
| [#6893](https://github.com/Flagsmith/flagsmith/issues/6893) | Toast dark mode support |
| [#6894](https://github.com/Flagsmith/flagsmith/issues/6894) | Checkbox and switch dark mode states |

**Foundation work in progress**:
- Semantic colour tokens + colour primitive palette on `chore/design-system-tokens` branch
- `@storybook/addon-a11y` installed on audit branch — every story has a WCAG accessibility panel

**Related efforts**:
- [#5746](https://github.com/Flagsmith/flagsmith/issues/5746) — TS migration epic (overlaps with legacy `.js` component findings)
- [#5921](https://github.com/Flagsmith/flagsmith/issues/5921) — UI improvements ([#6414](https://github.com/Flagsmith/flagsmith/issues/6414) overlaps with typography findings)
- [PR #6764](https://github.com/Flagsmith/flagsmith/pull/6764) — React 19 migration (resolves deprecated modal API)

---

### What Needs Team Discussion

These findings require architectural decisions before work can start:

1. **Dark mode strategy** — Continue with `.dark` SCSS selectors, or move to CSS custom properties (semantic tokens) as the single theming mechanism? The token approach is drafted but needs team buy-in before full adoption.

2. **Icon system** — Three systems coexist (Icon.tsx switch, svg/ directory, IonIcon). What's the target? Individual icon files with barrel export? Keep the `<Icon name="..." />` API?

3. **Modal system** — PR #6764 fixes the React compat issue, but the global imperative API (`openModal`/`openModal2` on `window`) and 14 duplicate confirmation modals remain. Worth introducing a context-based pattern?

4. **Form primitives** — `Input.js` handles 5 input types in one 231-line file. Introduce new typed building blocks (`TextInput`, `Checkbox`, `Radio`, etc.) and replace gradually?

5. **Typography and spacing** — 58 hardcoded `fontSize` values and off-grid spacing. Build custom tokens now, or wait for Tailwind adoption (which ships type scale and spacing utilities out of the box)?

6. **Table/list standardisation** — 9 `TableFilter*` components, 5+ row components, 5+ list components with no shared abstractions. Worth building a composable system, or too ambitious for now?

7. **Global component registry** — `project-components.js` attaches ~15 components to `window`. Removing it unblocks tree-shaking and TS migration, but requires adding explicit imports to every consuming `.js` file first.
