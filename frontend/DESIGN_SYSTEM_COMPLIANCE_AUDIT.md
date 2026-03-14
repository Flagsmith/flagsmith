# Design System Compliance Audit

**Date**: 2026-03-06
**Scope**: 525 component files across `web/components/`
**Prior work**: `DESIGN_SYSTEM_AUDIT.md` (2026-02-27), `DESIGN_SYSTEM_ISSUES.md` (2026-03-05), 28 issue files in `design-system-issues/`

---

## Executive Summary

**Components reviewed:** 525 files across 11 UI categories
**Issues found:** 85 tracked (21 P0 · 34 P1 · 30 P2)
**Quick wins completed:** 0 of 8
**Overall compliance score:** 47 / 100

A comprehensive audit was completed one week ago and 28 individual issue files were created. As of today, **none of the quick wins have been addressed**. The highest-ROI fixes — Icon.tsx dark mode, toast dark mode, and two known bugs — remain open and are blocking dark mode quality across the entire UI.

---

## Compliance Status by Category

### Naming Consistency

| Issue | Components Affected | Status |
|-------|---------------------|--------|
| 50 remaining `.js` files alongside `.tsx` counterparts | `Flex.js`, `Column.js`, `CreateProject.js`, `Payment.js`, `OrganisationSelect.js`, `ProjectSelect.js`, `FlagSelect.js`, and 43 others | Open |
| Duplicate coexisting files | `CreateWebhook.js` + `CreateWebhook.tsx`, `ErrorMessage.js` + `ErrorMessage.tsx`, `SuccessMessage.js` + `SuccessMessage.tsx` | Open |
| `InlineModal` named `displayName = 'Popover'` | `web/components/InlineModal.tsx` | Open |
| `inactiveClassName={activeClassName}` copy-paste bug | `web/components/navigation/SidebarLink.tsx:31` | Open — confirmed |

**Score: 4 / 10** — 10.5% of component files are unconverted JS. Three literal naming bugs are confirmed.

---

### Token Coverage

#### Colours

| Category | Defined tokens | Hardcoded values found | Status |
|----------|---------------|------------------------|--------|
| Brand colours | ✅ `$primary`, `$secondary`, etc. | 323 instances in TSX alone | Open |
| Grey scale | ⚠️ Ad hoc only | `#9DA4AE` (52 uses), `#656D7B` (44 uses) | Open |
| Alpha variants | ⚠️ Wrong base RGB | `rgba(149,108,255,…)` vs `#6837fc` actual | Open |
| Orphan hex | — | 30+ values with no token home | Open |

**Score: 3 / 10** — 280+ hardcoded hex instances in TSX. The grey scale has no formal primitives. Alpha variants use an incorrect base RGB that doesn't match their solid counterpart.

#### Typography

| Category | Status |
|----------|--------|
| Font size scale | Defined but bypassed in 6+ files |
| Font weight tokens | ❌ No general-purpose weight tokens (`$font-weight-*` missing) |
| Line-height tokens | Partially defined; 4 off-scale values in use |
| Inline style overrides | 50+ in admin dashboard alone |

**Score: 4 / 10** — No `$font-weight-semibold` token exists; `fontWeight: 600` appears hardcoded in 3 files. One confirmed invalid CSS value: `fontWeight: 'semi-bold'` in `SuccessMessage.tsx:44` (browser ignores it silently).

#### Spacing

| Category | Status |
|----------|--------|
| Base grid (8px) | Defined (`$spacer`) but widely ignored |
| Off-grid offenders | `5px` (10+ occurrences), `6px` (3+ files), `3px`, `15px`, `19px` |
| Chip margin inconsistency | `.chip-sm` uses `5px`, `.chip` uses `8px` |

**Score: 5 / 10** — `5px` is the single largest off-grid offender. A bulk replace of `5px → 4px` would be the highest-impact spacing fix.

---

### Component Completeness

#### Buttons — `web/components/base/forms/Button.tsx`

| Variant | Light mode | Dark mode | Score |
|---------|-----------|-----------|-------|
| primary | ✅ | ✅ | 10/10 |
| secondary | ✅ | ✅ | 10/10 |
| tertiary | ✅ | ❌ No override | 5/10 |
| danger | ✅ | ❌ Resolves to primary colour on hover | 3/10 |
| btn--transparent | ✅ | ❌ `rgba(0,0,0,0.1)` invisible on dark | 3/10 |
| btn--outline | ✅ | ⚠️ Hardcodes `background: white` | 6/10 |

Focus rings are explicitly removed via `btn:focus-visible { box-shadow: none }` — **WCAG 2.4.11 failure**.

#### Icons — `web/components/Icon.tsx` + `web/components/svg/`

| Issue | Count | Status |
|-------|-------|--------|
| `fill={fill \|\| '#1A2634'}` defaults | **41 instances** | Open — not fixed |
| `fill='#000000'` on expand icon | 1 | Open |
| `fill='rgb(104,55,252)'` hardcoded (link icon) | 1 | Open |
| SVG components not using `currentColor` | 19 of 19 | Open |
| Three separate icon systems | 1 | Open |

**Score: 1 / 10** — This is the single highest-priority item in the codebase. 41 icons are invisible in dark mode; the fix is a one-line change per icon.

#### Modals — `web/components/modals/`

| Issue | Status |
|-------|--------|
| 14 near-identical confirmation modals | Open |
| `openModal`/`closeModal` on `global` (deprecated React 18 API) | Open |
| `openModal2` anti-pattern acknowledged but in use | Open |
| `CreateProject.js` (class component, JS) | Open |
| `Payment.js` (class component, JS) | Open |

**Score: 4 / 10** — Core infrastructure uses a React 16-era imperative API. 14 confirmation modals each implement their own layout.

#### Notifications/Alerts

| Component | States | Variants | Dark mode | Score |
|-----------|--------|----------|-----------|-------|
| Toast | success, danger | 2 | ❌ No `.dark` block | 4/10 |
| ErrorMessage | — | 1 | ✅ | 7/10 |
| SuccessMessage | — | 1 | ✅ | 6/10 (fontWeight bug) |
| InfoMessage | — | 1 | ⚠️ Partial | 6/10 |
| WarningMessage | — | 1 | ❌ Icon invisible | 4/10 |

**Score: 5 / 10** — Toast has zero dark mode styles. `SuccessMessage` has an invalid CSS value (`fontWeight: 'semi-bold'`) that browsers silently ignore.

#### Forms/Inputs

| Issue | Severity |
|-------|----------|
| `input:read-only` hardcodes `#777`, no dark override | P0 |
| Checkbox focus/hover/disabled states missing in dark | P1 |
| Switch `:focus` not overridden in dark | P1 |
| Textarea border invisible in dark (`border-color: $input-bg-dark`) | P1 |
| Focus ring rgba uses wrong base (`rgba(51,102,255,…)` not `$primary`) | P2 |

**Score: 5 / 10**

#### Tables — `PanelSearch.tsx` + `web/components/tables/`

Reasonably well-structured. Filter components compose from a shared `TableFilter` base. `PanelSearch` is monolithic (20+ props) but functional.

**Score: 7 / 10**

#### Tabs — `web/components/navigation/TabMenu/`

Well-consolidated. Minor prop bloat (feature-specific `isRoles` prop).

**Score: 8 / 10**

#### Layout — `web/components/base/grid/`

`Panel.tsx` is a class component. `Flex.js` and `Column.js` are the oldest-style components in the codebase (class, `module.exports`, `propTypes`). `AccordionCard` imports `@material-ui/core` — the only Material UI usage, adding a heavy dependency for a single collapse animation.

**Score: 4 / 10**

---

### Accessibility (WCAG 2.1 AA)

| Check | Result |
|-------|--------|
| Secondary text contrast (both themes) | **FAIL** — `#656d7b` on white = 4.48:1; on dark = ~4.2:1. Both below 4.5:1. |
| Input border visibility | **FAIL** — 16% opacity border on white background |
| Button focus rings | **FAIL** — explicitly removed in `_buttons.scss` |
| Disabled element contrast | **FAIL** — `opacity: 0.32` on already-low-contrast elements |
| 54+ icons in dark mode | **FAIL** — invisible (`#1A2634` on `#101628`) |
| `WarningMessage` icon in dark mode | **FAIL** — icon fill invisible |

**Accessibility score: 3 / 10** — Multiple systemic WCAG AA failures, including in base tokens.

---

### Storybook / Documentation Coverage

| Category | Stories exist | A11y addon | Score |
|----------|--------------|------------|-------|
| Icons | ✅ | ❌ | 6/10 |
| Colours | ✅ | — | 7/10 |
| Buttons | ✅ | ❌ | 6/10 |
| Dark Mode Issues | ✅ | ❌ | 6/10 |
| Typography | ✅ | — | 7/10 |
| Forms/Inputs | ❌ | — | 0/10 |
| Modals | ❌ | — | 0/10 |
| Tables | ❌ | — | 0/10 |
| Tooltips | ❌ | — | 0/10 |

**Score: 4 / 10** — 6 of 9 audited categories have no Storybook stories. The accessibility addon (`@storybook/addon-a11y`) is not installed, so the existing stories cannot surface WCAG issues automatically.

---

## Priority Actions

### Unblocking (do this week)

These 5 items require less than 2 hours each and unlock dark mode quality across the entire UI.

1. **QW-1 — Icon.tsx default fills** `web/components/Icon.tsx`
   Replace 41 instances of `fill={fill || '#1A2634'}` with `fill={fill || 'currentColor'}`. Fixes dark mode for ~54 icons in one file change. See `design-system-issues/QW-1-icon-currentcolor.md`.

2. **QW-8 — SuccessMessage fontWeight bug** `web/components/messages/SuccessMessage.tsx:44`
   Change `fontWeight: 'semi-bold'` to `fontWeight: 600`. The string value is invalid CSS and silently ignored by browsers.

3. **ME-4 — Toast dark mode** `web/styles/components/_toast.scss`
   Add `.dark` block using existing `$success-solid-dark-alert` and `$danger-solid-dark-alert` tokens. See `design-system-issues/ME-4-toast-dark-mode.md`.

4. **Fix SidebarLink bugs** `web/components/navigation/SidebarLink.tsx`
   Line 31: `inactiveClassName={activeClassName}` should be `inactiveClassName={inactiveClassName}`. Line 42: remove hardcoded `fill={'#767D85'}`. These two bugs make inactive nav items render as active.

5. **Remove duplicate legacy components**
   Delete `web/components/ErrorMessage.js` and `web/components/SuccessMessage.js`. Both have TypeScript replacements in `web/components/messages/`.

### Medium term (this sprint)

6. **ME-2 — Button dark mode gaps** — Add `.dark` overrides for `btn-tertiary`, `btn-danger`, `btn--transparent` in `_buttons.scss`. See `design-system-issues/ME-2-button-dark-mode-gaps.md`.
7. **QW-3 — Chart axis dark mode** — Use `colorTextStandard`/`colorTextSecondary` from `common/theme` for Recharts tick fills. See `design-system-issues/QW-3-chart-axis-dark-mode.md`.
8. **ME-6 — Checkbox/switch dark mode focus states** — Complete missing `:focus`, `:hover`, `:disabled` dark overrides in `_input.scss` and `_switch.scss`.
9. **ME-9 — Expand accessibility coverage** — Install `@storybook/addon-a11y` and add it to the Storybook config. See `design-system-issues/ME-9-expand-a11y-coverage.md`.
10. **Standardise off-grid spacing** — Bulk replace `5px → 4px` in SCSS (highest-frequency offender, 10+ occurrences).

### Design system roadmap (next quarter)

These are tracked in the `LR-*` issue files in `design-system-issues/`:

- **LR-1** — Refactor `Icon.tsx`: extract inline SVGs to individual files, integrate `svg/` directory, retire IonIcon
- **LR-2** — Implement semantic colour token architecture (3-layer: primitives → semantic → component)
- **LR-3** — Migrate modal system from global imperative API to React context manager
- **LR-5** — Convert remaining 50 `.js` components to TypeScript
- **LR-6** — Define formal colour primitive palette (`$neutral-0` to `$neutral-950`, `$purple-*`)
- **LR-7** — Full dark mode audit pass across all SCSS files
- **LR-8** — Introduce `$font-weight-*` tokens; standardise typography scale

---

## Quick Reference: Score Summary

| Category | Score |
|----------|-------|
| Naming consistency | 4 / 10 |
| Colour token coverage | 3 / 10 |
| Typography tokens | 4 / 10 |
| Spacing tokens | 5 / 10 |
| Button component | 5 / 10 |
| Icon component | 1 / 10 |
| Modal system | 4 / 10 |
| Notifications/Alerts | 5 / 10 |
| Forms/Inputs | 5 / 10 |
| Tables | 7 / 10 |
| Tabs | 8 / 10 |
| Layout | 4 / 10 |
| Accessibility (WCAG) | 3 / 10 |
| Storybook coverage | 4 / 10 |
| **Overall** | **47 / 100** |

---

*For detailed findings per issue, see the `design-system-issues/` directory. For colour token architecture, see `COLOUR_TOKEN_PLAN.md`. For the full component-by-component breakdown, see `DESIGN_SYSTEM_AUDIT.md`.*
