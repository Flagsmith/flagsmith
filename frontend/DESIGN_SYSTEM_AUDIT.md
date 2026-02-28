# Flagsmith Frontend Design System Audit

**Issue**: #6606
**Date**: 2026-02-27
**Scope**: Code-first audit of token misuse, dark mode gaps, and component fragmentation

---

## Executive Summary

This audit scanned the Flagsmith frontend codebase for design system inconsistencies across 7 areas (colours, typography, spacing, buttons, forms, icons, notifications) and catalogued 11 UI component categories.

### Key findings

| Severity | Count | Description |
|----------|-------|-------------|
| **P0** | 21 | Broken in dark mode or accessibility issue |
| **P1** | 34 | Visual inconsistency with the token system |
| **P2** | 30 | Token hygiene (hardcoded value that should use a variable) |

### Top 5 fixes by impact

1. **Icon.tsx default fills** — ~60 icons default to `#1A2634` (near-black), invisible in dark mode. Switching to `currentColor` would fix all at once.
2. **Feature pipeline status** — Entire release pipeline visualisation is broken in dark mode (white circles, grey lines on dark background).
3. **Chart components** — All 4 Recharts-based charts use hardcoded light-mode axis/grid colours. Need dark mode conditionals.
4. **Button variants missing dark mode** — `btn-tertiary`, `btn-danger`, and `btn--transparent` have no dark mode overrides.
5. **Toast notifications** — No dark mode styles at all.

### Top 5 consolidation opportunities

1. **Icons** — Refactor the monolithic `Icon.tsx` (70 inline SVGs), unify with 19 separate SVG components and `IonIcon` usage.
2. **Modals** — Migrate from global imperative API, consolidate 13+ near-identical confirmation modals.
3. **Notifications** — Remove 2 duplicate legacy `.js` message components, unify 4 alert variants into a single `Alert` component.
4. **Menus/Dropdowns** — Extract a shared dropdown primitive from 4 independent implementations.
5. **Layout** — Convert legacy JS class components (`Flex.js`, `Column.js`), remove Material UI dependency from `AccordionCard`.

---

# Part A — Component Inventory

## 1. Modals/Dialogs

**Files**: 52 files in `web/components/modals/`

**Base infrastructure** (6 files):
- `web/components/modals/base/Modal.tsx` — Core modal system: `openModal`, `openModal2`, `openConfirm` globals
- `web/components/modals/base/ModalDefault.tsx` — Standard modal wrapper using reactstrap `Modal`
- `web/components/modals/base/ModalConfirm.tsx` — Confirmation dialog (yes/no with danger variant)
- `web/components/modals/base/ModalAlert.tsx` — Simple alert modal with single OK button
- `web/components/modals/base/ModalHeader.tsx` — Custom header with close button
- `web/components/modals/base/ModalClose.tsx` — Close button component

**Confirmation modals** (13 files):
`ConfirmCloneSegment`, `ConfirmDeleteAccount`, `ConfirmDeleteRole`, `ConfirmHideFlags`, `ConfirmRemoveAuditWebhook`, `ConfirmRemoveEnvironment`, `ConfirmRemoveFeature`, `ConfirmRemoveOrganisation`, `ConfirmRemoveProject`, `ConfirmRemoveSegment`, `ConfirmRemoveTrait`, `ConfirmRemoveWebhook`, `ConfirmToggleFeature`, `ConfirmToggleEnvFeature`

**Creation/editing modals** (15+ files):
`CreateAuditLogWebhook`, `CreateEditIntegrationModal`, `CreateGroup`, `CreateMetadataField`, `CreateOrganisation`, `CreateProject.js`, `CreateRole`, `CreateSAML`, `CreateSegment`, `CreateTrait`, `CreateUser`, `CreateWebhook.js`, `CreateWebhook.tsx`, `ChangeEmailAddress`, `ChangeRequestModal`, `ForgotPasswordModal`, `InviteUsers`, `Payment.js`

**Complex multi-tab modals** (2 subdirectories):
- `create-feature/` (7 files)
- `create-experiment/` (2 files)

**Also**: `web/components/InlineModal.tsx` — separate inline (non-overlay) modal

**Variant count**: 4 base modal types (ModalDefault, ModalConfirm, ModalAlert, InlineModal)

**Pattern issues**:
- Modal system uses deprecated `react-dom` `render`/`unmountComponentAtNode` (removed in React 18) and attaches `openModal`/`closeModal` to `global`
- `openModal2` exists for stacking modals, acknowledged as a pattern to avoid
- Duplicate: `CreateWebhook.js` and `CreateWebhook.tsx` coexist
- `CreateProject.js` and `Payment.js` remain as unconverted JS class components
- 13+ confirmation modals each implement their own layout rather than composing from a shared template
- `InlineModal` has `displayName = 'Popover'`, which is misleading

**Consolidation notes**: The 13+ confirmation modals follow nearly identical patterns (title, message, ModalHR, Cancel/Confirm buttons) and could be a single configurable `ConfirmModal`. The global `openModal`/`closeModal` imperative API should migrate to a React context-based modal manager.

---

## 2. Menus/Dropdowns

**Files**:
- `web/components/base/DropdownMenu.tsx` — Icon-triggered vertical "more" menu using portal positioning
- `web/components/base/forms/ButtonDropdown.tsx` — Split button with dropdown actions
- `web/components/base/Popover.tsx` — Toggle-based popover using `FocusMonitor` HOC
- `web/components/InlineModal.tsx` — Panel-style dropdown (used by TableFilter)

**Variant count**: 4 distinct dropdown/overlay patterns

**Pattern issues**:
- `DropdownMenu` and `ButtonDropdown` both implement their own outside-click handling, positioning logic, and dropdown rendering independently
- Both share CSS class `feature-action__list` / `feature-action__item` but are not composed from shared primitives
- `Popover` uses a different mechanism (`FocusMonitor` HOC) for state
- `InlineModal` functions as another dropdown variant but is named "Modal"

**Consolidation notes**: A single base `Dropdown`/`Popover` primitive with portal support, outside-click handling, and positioning could replace all four.

---

## 3. Selects

**Files**: 28 files (2 base + 26 domain-specific)

**Base**: `web/components/base/select/SearchableSelect.tsx`, `web/components/base/select/multi-select/MultiSelect.tsx`

**Domain-specific** (26): `EnvironmentSelect`, `EnvironmentTagSelect`, `OrgEnvironmentSelect`, `OrganisationSelect.js`, `ProjectSelect.js`, `FlagSelect.js`, `SegmentSelect`, `GroupSelect`, `ConnectedGroupSelect`, `MyGroupsSelect`, `UserSelect`, `RolesSelect`, `MyRoleSelect`, `IntegrationSelect`, `DateSelect`, `ConversionEventSelect`, `IdentitySelect`, `GitHubRepositoriesSelect`, `GitHubResourcesSelect`, `MyRepositoriesSelect`, `RepositoriesSelect`, `ColourSelect`, `SupportedContentTypesSelect`, `SelectOrgAndProject`, `RuleConditionPropertySelect`, `EnvironmentSelectDropdown`

**Pattern issues**: 3 remain as `.js` files. Potential overlap between `GroupSelect`/`ConnectedGroupSelect`/`MyGroupsSelect`.

**Consolidation notes**: The large number of domain selects is reasonable since each encapsulates data fetching. Ensure all consistently use `SearchableSelect` or `MultiSelect` as their base. Convert `.js` files to TypeScript.

---

## 4. Toasts/Notifications

**Files**:

Toast system:
- `web/project/toast.tsx` — Global toast with `success` and `danger` themes, attached to `window.toast`

Inline alert components (6 files, 2 duplicated):
- `web/components/messages/ErrorMessage.tsx` — TypeScript FC version
- `web/components/messages/SuccessMessage.tsx` — TypeScript FC version
- `web/components/ErrorMessage.js` — Legacy class component duplicate
- `web/components/SuccessMessage.js` — Legacy class component duplicate
- `web/components/InfoMessage.tsx` — Info alert with collapsible content
- `web/components/WarningMessage.tsx` — Warning alert

**Variant count**: 1 toast system (2 themes) + 4 inline alert variants

**Pattern issues**:
- `ErrorMessage` and `SuccessMessage` each exist in two versions (legacy `.js` + modern `.tsx`)
- Toast only supports `success` and `danger` — no `info` or `warning` toast themes
- Toast is attached to `window` as a global function

**Consolidation notes**: Remove legacy `.js` duplicates. Unify all inline alerts into a single `Alert` component with a `variant` prop. Add `info`/`warning` themes to the toast system.

---

## 5. Tables & Filters

**Files**: 1 core table + 9 filter components

**Core**: `web/components/PanelSearch.tsx` — Searchable, paginated, sortable list using `react-virtualized`

**Filters** (in `web/components/tables/`):
`TableFilter`, `TableFilterItem`, `TableFilterOptions`, `TableGroupsFilter`, `TableOwnerFilter`, `TableSearchFilter`, `TableSortFilter`, `TableTagFilter`, `TableValueFilter`

**Pattern issues**: `PanelSearch` is monolithic (20+ props). Uses `react-virtualized` (older library).

**Consolidation notes**: Filter components are well-structured around `TableFilter` base. Consider decomposing `PanelSearch` into smaller composable pieces.

---

## 6. Tabs

**Files**:
- `web/components/navigation/TabMenu/Tabs.tsx` — Main container with `tab` and `pill` themes, URL param sync, overflow handling
- `web/components/navigation/TabMenu/TabItem.tsx` — Tab content wrapper
- `web/components/navigation/TabMenu/TabButton.tsx` — Tab button using `Button` component

**Variant count**: 1 implementation with 2 themes

**Pattern issues**: Well-consolidated. Minor prop bloat (13 props including feature-specific `isRoles`).

---

## 7. Buttons

**Files**: `web/components/base/forms/Button.tsx`

**Themes** (9): `primary`, `secondary`, `tertiary`, `danger`, `success`, `text`, `outline`, `icon`, `project`

**Sizes** (5): `default`, `large`, `small`, `xSmall`, `xxSmall`

**Pattern issues**: Doubles as a link when `href` is provided. Plan-gating (`feature` prop) is baked in rather than being a wrapper.

**Consolidation notes**: Clean system overall. Consider extracting link behaviour and plan-gating concern.

---

## 8. Icons

**Files**:
- `web/components/Icon.tsx` — 70 inline SVG icons in a switch statement
- `web/components/svg/` — 19 standalone SVG components: `ArrowUpIcon`, `AuditLogIcon`, `CaretDownIcon`, `CaretRightIcon`, `DocumentationIcon`, `DropIcon`, `EnvironmentSettingsIcon`, `FeaturesIcon`, `LogoutIcon`, `NavIconSmall`, `OrgSettingsIcon`, `PlayIcon`, `PlusIcon`, `ProjectSettingsIcon`, `SegmentsIcon`, `SparklesIcon`, `UpgradeIcon`, `UserSettingsIcon`, `UsersIcon`

**Also**: `@ionic/react` `IonIcon` used in `InfoMessage`, `SuccessMessage`, `AccordionCard` — a third icon system.

**Variant count**: 70 inline + 19 SVG files + IonIcon = 3 separate icon systems, ~89 total icons

**Pattern issues**:
- `Icon.tsx` is extremely large because every icon is an inline SVG in a switch
- The 19 `svg/` components are completely separate, not accessible via `Icon.tsx`
- `IonIcon` adds a third, heavy dependency for just a few icons

**Consolidation notes**: Highest priority. Refactor `Icon.tsx` to import individual SVG files. Integrate `svg/` components. Migrate `IonIcon` usage. Consider SVG sprites or individual imports for tree-shaking.

---

## 9. Empty States

**Files**:
- `web/components/EmptyState.tsx` — Generic empty state with icon, title, description, docs link, action
- `web/components/pages/features/components/FeaturesEmptyState.tsx` — Specialised onboarding variant

**Variant count**: 2 (1 generic + 1 specialised)

**Pattern issues**: `FeaturesEmptyState` does not use the generic `EmptyState`. Reasonable separation since it serves a different purpose (onboarding walkthrough).

---

## 10. Tooltips

**Files**:
- `web/components/Tooltip.tsx` — Main tooltip using `react-tooltip`, with HTML sanitisation and portal support
- `web/components/base/LabelWithTooltip.tsx` — Convenience wrapper: label + info icon tooltip

**Variant count**: 2 (1 core + 1 convenience wrapper)

**Pattern issues**:
- Inverted API: `title` is the trigger element and `children` is the tooltip content
- `children` rendered via `dangerouslySetInnerHTML` (sanitised with DOMPurify)
- New `id` (GUID) generated on every render
- `TooltipPortal` creates DOM nodes but never removes them (memory leak)

---

## 11. Layout

**Files**:

Grid primitives in `web/components/base/grid/`:
- `Panel.tsx` — Panel with optional title/action header (class component)
- `FormGroup.tsx` — Simple `.form-group` wrapper
- `Row.tsx` — Flex row with `space` and `noWrap` props
- `Flex.js` — Legacy flex wrapper (class component, `module.exports`)
- `Column.js` — Legacy flex-column wrapper (class component, `module.exports`)

Composite:
- `web/components/PanelSearch.tsx` — Searchable panel/list
- `web/components/base/accordion/AccordionCard.tsx` — Collapsible card using Material UI's `Collapse` and `IconButton`

**Pattern issues**:
- `Panel` is a class component (`PureComponent`)
- `Flex.js` and `Column.js` are the oldest-style components (class, `module.exports`, `propTypes`, globals)
- `AccordionCard` depends on `@material-ui/core` — the only place Material UI appears, adding a heavy dependency

**Consolidation notes**: Convert `Panel`, `Flex.js`, `Column.js` to TypeScript FCs. Replace Material UI in `AccordionCard` with CSS transition or `<details>`/`<summary>`. Consider removing `Flex`/`Column` given modern CSS utility classes.

---

# Part B — Token & Consistency Findings

## 1. Colours

### P0 — Broken Dark Mode / Accessibility

**1.1 Icon.tsx — ~60 icons default to `#1A2634` fill, invisible in dark mode (CRITICAL)**
- `web/components/Icon.tsx` — lines 225, 482, 559, 578, 597, 616, 636, 655, 674, 693, 712, 731, 751, 771, 790, 809, 828, 867, 888, 908, 928, 1011, 1031, 1050, 1069, 1089, 1108, 1127, 1146, 1165, 1185, 1205, 1224, 1244, 1251, 1258, 1278, 1328, 1345, 1365, 1406
- Pattern: `fill={fill || '#1A2634'}` — dark navy fill is invisible on dark backgrounds unless every caller passes an explicit fill
- **Fix**: Switch default to `currentColor` or add `getDarkMode()` awareness

**1.2 Icon.tsx — 3 icons hardcode `#163251`, an orphan colour**
- `web/components/Icon.tsx:237,245,253` — `fill || '#163251'` — not in any token

**1.3 Icon.tsx `expand` icon defaults to `fill='#000000'`**
- `web/components/Icon.tsx:1502` — black fill invisible on dark backgrounds

**1.4 Feature pipeline status — entire component has no `.dark` override**
- `web/styles/components/_feature-pipeline-status.scss:2,4,16,20,30,39,43,52`
- Hardcoded: `white` (bg), `#AAA` (border/bg), `#6837fc` (border), `#53af41` (border/bg)
- White circles and grey lines invisible on dark backgrounds

**1.5 FeaturesPage action item — hardcoded dark text**
- `web/styles/project/_FeaturesPage.scss:42` — `color: #2d3443`
- Nearly invisible on dark backgrounds. Value doesn't match `$body-color` (`#1a2634`)

**1.6 Striped section — no dark mode override**
- `web/styles/styles.scss:66` — `background-color: #f7f7f7`
- Should use `$bg-light200`; light grey will clash with dark body

**1.7 Alert bar — orphan colour, no dark override**
- `web/styles/styles.scss:172,175` — `color: #fff`, `background-color: #384f68`
- `#384f68` not in any token definition

**1.8 Modal tab dropdown hover — wrong purple, no dark override**
- `web/styles/project/_modals.scss:294` — `background-color: #6610f210 !important`
- `#6610f2` does not match `$primary` (`#6837fc`); non-standard 8-digit hex

**1.9 BooleanDotIndicator — orphan disabled colour**
- `web/components/BooleanDotIndicator.tsx:4` — `enabled ? '#6837fc' : '#dbdcdf'`
- `#dbdcdf` is an orphan; disabled dot barely visible in dark mode

**1.10 DateSelect — dark fill invisible**
- `web/components/DateSelect.tsx:136` — `fill={isOpen ? '#1A2634' : '#9DA4AE'}`
- `#1A2634` invisible on dark backgrounds

### P1 — Visual Inconsistency

**1.11 Charts use hardcoded light-mode colours (4 files)**
- `web/components/organisation-settings/usage/OrganisationUsage.container.tsx:44-63`
- `web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx:42-62`
- `web/components/feature-page/FeatureNavTab/FeatureAnalytics.tsx:101-107`
- `web/components/modals/create-experiment/ExperimentResultsTab.tsx:81-129`
- Hardcoded: `stroke='#EFF1F4'` (grid), `fill: '#656D7B'` (tick), `fill: '#1A2634'` (tick)
- All charts render light-mode colours on dark backgrounds

**1.12 `#53af41` orphan green used across release pipeline**
- `web/components/release-pipelines/StageStatus.tsx:91`
- `web/components/release-pipelines/StageSummaryData.tsx:57,79`
- `web/styles/components/_feature-pipeline-status.scss:20,39,52`
- Not in token palette; closest is `$success` (`#27ab95`)

**1.13 Unread badge — off-brand primary**
- `web/styles/project/_utils.scss:155` — `background: #7b51fb`
- Should use `$primary` (`#6837fc`)

**1.14 Button remove hover — inconsistent red**
- `web/styles/project/_buttons.scss:183` — `fill: #d93939`
- Neither `$danger` nor `$btn-danger-hover`; a third red shade

**1.15 Panel change-request — raw rgba with wrong base colour**
- `web/styles/components/_panel.scss:225,228-229,233,240`
- `rgba(102, 51, 255, 0.08)` uses `#6633ff` not `#6837fc`; should use `$primary-alfa-8`

**1.16 ArrowUpIcon / DocumentationIcon / Logo — off-brand purple**
- `web/components/svg/ArrowUpIcon.tsx:18`, `web/components/svg/DocumentationIcon.tsx:23`, `web/components/Logo.tsx:20`
- `fill='#63f'` = `#6633ff`, not `$primary` (`#6837fc`)

**1.17 `#53af41` orphan green in CreatePipelineStage**
- `web/components/release-pipelines/CreatePipelineStage.tsx:180,184,187`
- Hardcoded danger colour with inline box-shadow

**1.18 VCSProviderTag — orphan dark colour**
- `web/components/tags/VCSProviderTag.tsx:47` — `backgroundColor: isWarning ? '#ff9f43' : '#343a40'`
- `#343a40` not in any token

**1.19 PanelSearch — inline style colours bypass dark mode**
- `web/components/PanelSearch.tsx:225,230` — `style={{ color: isActive ? '#6837FC' : '#656d7b' }}`
- Should use CSS classes with `.dark` support

**1.20 FeaturesPage hover uses full `$primary` in dark mode**
- `web/styles/project/_FeaturesPage.scss:72` — `.dark .feature-action__item:hover` uses `background: $primary`
- Light mode uses `$bg-light200`; dark mode is jarring/oversaturated

**1.21 Step list — orphan colour**
- `web/styles/project/_lists.scss:9,14,21` — `#2e2e2e` (border and background)
- Not in the token palette

### P2 — Token Hygiene

**1.22 ~35 TSX files hardcode `fill='#9DA4AE'` / `fill='#656D7B'` / `fill='#6837FC'`**
- Values match tokens (`$text-icon-light-grey`, `$text-icon-grey`, `$primary`) but bypass the token system
- If token values change, these will not update
- Files include: `ChangeRequestsList`, `SegmentOverrideActions`, `TopNavbar`, `AccountDropdown`, `SDKKeysPage`, `RolesTable`, `SamlTab`, `GroupSelect`, `UserGroupList`, and many more

**1.23 Admin dashboard tables — ~20 orphan colours in inline styles**
- `web/components/pages/admin-dashboard/components/OrganisationUsageTable.tsx`
- `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx`
- `web/components/pages/admin-dashboard/components/IntegrationAdoptionTable.tsx`
- Colours: `#f8f9fa`, `#fafbfc`, `#eee`, `#e74c3c`, `#e9ecef`, `#e0e0e0`, `#f4f5f7`

**1.24 Language colour blocks — intentional but undocumented**
- `web/styles/components/_color-block.scss:21-36` — GitHub language colours (`#3572A5`, `#f1e05a`, etc.)
- Should be extracted to named variables

**1.25 GitHub icon colours — brand colours**
- `web/components/Icon.tsx:1417-1488` — `#8957e5`, `#238636`, `#da3633`
- Likely intentional but should be named constants

**1.26 SidebarLink — orphan muted colour**
- `web/components/navigation/SidebarLink.tsx:42` — `fill={'#767D85'}`
- Closest token is `$text-icon-grey` (`#656D7B`)

**1.27 CreateFeature tab — orphan purple**
- `web/components/modals/create-feature/tabs/CreateFeature.tsx:107` — `color: '#6A52CF'`

---

## 2. Typography

### Systemic Issues

**Missing general-purpose font-weight tokens**: The token system only defines weight variables scoped to components (`$btn-font-weight: 700`, `$input-font-weight: 500`). No general tokens like `$font-weight-regular: 400`, `$font-weight-medium: 500`, `$font-weight-semibold: 600`, `$font-weight-bold: 700`.

**Off-scale values indicate design drift**: Values like 9px, 10px, 15px, 17px, 19px, 20px, 22px, 34px appear but have no corresponding token.

### P0

**2.1 FeaturesPage — hardcoded dark text colour**
- `web/styles/project/_FeaturesPage.scss:42` — `color: #2d3443` with no adequate dark mode override
- (Also listed under Colours 1.5)

**2.2 Dark mode text colour gaps in inline styles**
- `web/components/pages/admin-dashboard/components/OrganisationUsageTable.tsx:21` — `color: '#e74c3c'`
- `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx:404` — `color: '#27AB95'`
- `web/components/tags/TagFilter.tsx:45` — `color: '#656D7B'`
- `web/components/navigation/AccountDropdown.tsx:80` — `color: '#656D7B'`
- Inline colours cannot respond to dark mode

### P1 — Hardcoded Font-Size Off-Scale

| File | Line | Value | Notes |
|------|------|-------|-------|
| `web/styles/3rdParty/_hljs.scss` | 100 | `font-size: 17px` | Between `$h6` (16px) and `$h5` (18px) |
| `web/styles/3rdParty/_hw-badge.scss` | 13 | `font-size: 9px` | Below `$font-caption-xs` (11px) |
| `web/styles/project/_utils.scss` | 164 | `font-size: 10px` | Below scale |
| `web/styles/project/_alert.scss` | 52 | `font-size: 20px` | Between `$h5` (18px) and `$h4` (24px) |
| `web/styles/project/_icons.scss` | 9 | `font-size: 19px` | Between `$h5` (18px) and `$h4` (24px) |
| `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx` | 282 | `fontSize: 10` | Below scale |

### P1 — Hardcoded Line-Height Off-Scale

| File | Line | Value | Notes |
|------|------|-------|-------|
| `web/styles/components/_input.scss` | 71 | `line-height: 22px` | Between `$line-height-sm` (20px) and `$line-height-lg` (24px) |
| `web/styles/components/_paging.scss` | 14 | `line-height: 34px` | Above `$line-height-xlg` (28px) |
| `web/styles/components/_tabs.scss` | 167 | `line-height: 15px` | Below `$line-height-xxsm` (16px) |
| `web/styles/project/_utils.scss` | 163 | `line-height: 14px` | Below scale |

### P1 — Inline Font Weight 600 (no token exists)

| File | Line | Value |
|------|------|-------|
| `web/components/pages/admin-dashboard/components/OrganisationUsageTable.tsx` | 21, 27 | `fontWeight: 600` |
| `web/components/pages/admin-dashboard/components/ReleasePipelineStatsTable.tsx` | 283 | `fontWeight: 600` |
| `web/components/navigation/AccountDropdown.tsx` | 83 | `fontWeight: 600` |

### P2 — Hardcoded Font-Size On-Scale

| File | Line | Value | Token |
|------|------|-------|-------|
| `web/styles/styles.scss` | 185 | `font-size: 30px` | `$h3-font-size` |
| `web/styles/styles.scss` | 191 | `font-size: 14px` | `$font-size-base` |
| `web/styles/styles.scss` | 193 | `font-size: 11px` | `$font-caption-xs` |
| `web/styles/components/_switch.scss` | 79 | `font-size: 14px` | `$font-size-base` |
| `web/styles/components/_metrics.scss` | 15 | `font-size: 16px` | `$h6-font-size` |
| `web/styles/project/_type.scss` | 104 | `font-size: 0.75rem` | `$font-caption-sm` (12px) |

### P2 — Admin Dashboard Inline fontSize Hotspot

The files under `web/components/pages/admin-dashboard/components/` contain over 50 inline `fontSize` overrides across `OrganisationUsageTable.tsx`, `ReleasePipelineStatsTable.tsx`, and `IntegrationAdoptionTable.tsx`. These bypass both the SCSS token system and dark mode theming. This is the single largest area of typography token misuse.

---

## 3. Spacing

### P1 — Off-Grid Spacing Values

| File | Line | Value | Issue |
|------|------|-------|-------|
| `web/styles/project/_buttons.scss` | 149 | `padding: 19px 0 18px 0` | Both off-grid; asymmetric by 1px |
| `web/styles/styles.scss` | 173 | `padding: 15px` | Off-grid; should be 16px (`$spacer`) |
| `web/styles/styles.scss` | 206 | `padding: 10px 10px 5px 0` | 10px and 5px both off-grid |
| `web/styles/components/_chip.scss` | 42 | `padding: 5px 12px` | 5px off-grid (chip is heavily reused) |
| `web/styles/components/_chip.scss` | 84 | `padding: 3px 8px` | 3px off-grid |
| `web/styles/components/_chip.scss` | 85, 89, 101, 113 | `margin-right: 5px` | 5px off-grid (repeated 4 times) |
| `web/styles/project/_FeaturesPage.scss` | 11, 24 | `margin-top: 6px`, `margin-bottom: 6px` | 6px off-grid |
| `web/styles/components/_metrics.scss` | 11 | `margin-bottom: 6px` | 6px off-grid |
| `web/styles/project/_forms.scss` | 149 | `margin-bottom: 6px` | 6px off-grid |
| `web/styles/project/_alert.scss` | 4, 7, 14 | `margin-top: 60px, 130px, 70px` | Layout offsets coupled to fixed header height |

### P1 — Inconsistent Spacing Across Similar Components

**Chip margin-right inconsistency**:
- `.chip`: `margin-right: 0.5rem` (8px) — good
- `.chip--sm`: `margin-right: 5px` — off-grid
- `.chip--xs`: `margin-right: 5px` — off-grid
- `.chip .margin-right`: `12px` — different value entirely

### P2 — On-Grid But Hardcoded

| File | Line | Value | Notes |
|------|------|-------|-------|
| `web/styles/project/_panel.scss` | 43 | `padding: 20px` | Should use `$spacer * 1.25` |
| `web/styles/project/_modals.scss` | 106 | `padding: 20px` | Inconsistent with `$modal-body-padding-y` (24px) |
| `web/styles/project/_utils.scss` | 78, 82 | `margin-top: 20px`, `margin-bottom: 20px` | Custom utility duplicating Bootstrap `.mt-4`/`.mb-4` |
| `web/styles/project/_utils.scss` | 175 | `padding: 10px` | Off-grid |
| `web/styles/styles.scss` | 161 | `margin-left: 10px` | Off-grid |
| `web/styles/3rdParty/_hljs.scss` | 184, 186 | `padding: 7px 12px`, `margin-right: 5px` | Off-grid |
| `web/styles/components/_switch.scss` | 80 | `padding-left: 10px` | Off-grid |

### Systemic Patterns

- **5px is the most common off-grid offender** (10+ occurrences). Bulk replace to 4px would be highest-impact single change.
- **12px is an unofficial spacing token** used 5+ times for `margin-right`. Should be formalised as `$spacer * 0.75`.
- **6px appears as a small vertical spacer** in 3+ files. Standardise to 4px or 8px.

---

## 4. Button Styles

### P0

**4.1 `btn--transparent` hover — no dark mode override**
- `web/styles/project/_buttons.scss:155` — hover uses `rgba(0,0,0,0.1)`, nearly invisible on dark backgrounds

**4.2 `btn-tertiary` — no dark mode override**
- `web/styles/project/_buttons.scss:113-127` — gold/yellow variant with `$primary900` text. Not overridden in `.dark` block (lines 432-563). May be unreadable on dark backgrounds.

**4.3 `btn-danger` — dark hover resolves to primary colour**
- `web/styles/project/_buttons.scss:32-43` — `.dark` block does not include `btn-danger` override. Generic `.dark .btn:hover` (line 436) overwrites danger-specific hover with primary colour.

### P1

**4.4 `btn--outline` hardcodes `background: white`**
- `web/styles/project/_buttons.scss:59` — should be `$bg-light100` or `$input-bg`

**4.5 `btn-link .dark-link` — invisible in dark mode**
- `web/styles/project/_buttons.scss:379` — `.dark-link` sets `color: $body-color` (dark text), no dark override

### P2

**4.6 `btn--remove` hover — orphan red `#d93939`**
- `web/styles/project/_buttons.scss:183` — not a design token

**4.7 Excessive `!important` in button styles**
- `web/styles/project/_buttons.scss:60,86-87,100-101,104,109,114,201,209,228,238,252-257`
- At least 15 `!important` declarations creating specificity debt

**4.8 Inline style overrides on Button components in TSX**
- Multiple TSX files apply `style={{...}}` directly on `<Button>` components, bypassing the theming system

---

## 5. Form Inputs

### P0

**5.1 `input:read-only` — hardcoded `#777`, no dark mode**
- `web/styles/components/_input.scss:96` — `color: #777` on dark background = low contrast

### P1

**5.2 Dark mode checkbox focus/hover/disabled states missing**
- `web/styles/components/_input.scss:280-293` — dark block only covers base and checked states. Focus box-shadow (blue) appears on dark background with white border.

**5.3 Dark mode switch `:focus` not overridden**
- `web/styles/components/_switch.scss:100-121` — focus ring colour not adjusted for dark backgrounds

**5.4 Textarea border invisible in dark mode**
- `web/styles/components/_input.scss:176` — `border-color: $input-bg-dark` makes border same colour as background, unlike input field treatment

### P2

**5.5 Autofill input colour — raw rgba**
- `web/styles/components/_input.scss:125` — `rgba(0, 0, 0, 0.870588)` should use `$body-color`

**5.6 Checkbox focus box-shadow — raw rgba**
- `web/styles/components/_input.scss:308` — `rgba(51, 102, 255, 0.32)` should use a token derived from `$primary`

**5.7 Switch focus ring — raw rgba**
- `web/styles/components/_switch.scss:16` — same `rgba(51, 102, 255, 0.32)` as checkbox. Should be a shared focus-ring token.

**5.8 No dedicated `_checkbox.scss` or `_select.scss` files**
- Checkbox styles split across `_input.scss` and `_forms.scss`; Select in `3rdParty/_react-select.scss`. Fragmented.

---

## 6. Icons

### P0

**6.1 ~60 icons default to `#1A2634` fill — invisible in dark mode**
- `web/components/Icon.tsx` — pattern `fill={fill || '#1A2634'}` across ~60 icon cases
- (Also listed under Colours 1.1)

**6.2 `link` icon hardcodes fill, ignores fill prop**
- `web/components/Icon.tsx:133` — `fill='rgb(104, 55, 252)'` — cannot be themed

**6.3 `github` icon hardcodes `#1A2634`, ignores fill prop**
- `web/components/Icon.tsx:335` — invisible on dark backgrounds

**6.4 `expand` icon defaults to `#000000`**
- `web/components/Icon.tsx:1502` — invisible on dark backgrounds

### P1

**6.5 Git/PR status icons hardcode colours, ignore fill prop**
- `web/components/Icon.tsx:1417,1431,1446,1460,1474,1488` — `#8957e5`, `#238636`, `#da3633`, `#1A2634`

**6.6 All 19 SVG components hardcode fills**
- `web/components/svg/PlayIcon.tsx` (`#f27157`), `CaretRightIcon.tsx` (`#000`), `ArrowUpIcon.tsx` (`#63f`), `DocumentationIcon.tsx` (`#63f`), `DropIcon.tsx` (`#9DA4AE`), etc.
- None use `currentColor`. `CaretRightIcon` with `#000` is invisible in dark mode if used outside sidebar.

### P2

**6.7 No standardised icon sizing system**
- `web/styles/project/_icons.scss` (20 lines) — only defines `.icon--green`, `.icon--tooltip` (base size), `.icon--new-tooltip` (hardcoded 19px)
- Icon sizes are set ad-hoc via `width` prop on `Icon.tsx` (default 24, callers use 16, 20, 22)

---

## 7. Notifications

### P0

**7.1 Toast has no dark mode styles**
- `web/styles/components/_toast.scss` (55 lines) — uses `$success-solid-alert` background and `$success` border with no `.dark` override block

**7.2 Dark mode `alert-success` title/strong text uses dark colour on dark background**
- `web/styles/project/_alert.scss:93-101` — `alert-info` overrides `.title`/`strong` to `$text-icon-light` in dark mode, but `alert-success` does not. Title/strong remain `$body-color`.

**7.3 WarningMessage icon invisible in dark mode**
- `web/components/WarningMessage.tsx:26` — `<Icon name='warning' />` without explicit fill. Icon defaults to `#1A2634`, invisible on dark backgrounds.

### P1

**7.4 Dark mode alert border colours not adjusted**
- `web/styles/project/_alert.scss:86-109` — dark block overrides `background-color` for all 4 alert variants but not `border-color`. Light-mode borders may mismatch dark backgrounds.

**7.5 SuccessMessage uses invalid CSS `fontWeight: 'semi-bold'`**
- `web/components/messages/SuccessMessage.tsx:44` — `style={{ fontWeight: 'semi-bold' }}` is not valid CSS. Browser ignores it; title renders at default weight. Should be `600`.

### P2

**7.6 SuccessMessage hardcodes icon fill**
- `web/components/messages/SuccessMessage.tsx:41` — `<Icon fill='#27AB95' name='checkmark-circle' />`

**7.7 InfoMessage hardcodes icon fill**
- `web/components/InfoMessage.tsx:75` — `<Icon fill={'#0AADDF'} name={icon || 'info'} />`

---

## Recommendations

### Quick Wins (< 1 day each)

1. **Fix Icon.tsx default fills** — Change `fill={fill || '#1A2634'}` to `fill={fill || 'currentColor'}` across all ~60 icons. Single-file change with massive dark mode impact.
2. **Add `.dark` block to `_toast.scss`** — Use existing `$success-solid-dark-alert` and `$danger-solid-dark-alert` tokens.
3. **Fix `SuccessMessage` fontWeight** — Change `'semi-bold'` to `600`.
4. **Remove duplicate `.js` message components** — Delete `web/components/ErrorMessage.js` and `web/components/SuccessMessage.js`.
5. **Fix WarningMessage icon** — Add `fill='currentColor'` prop.

### Medium-Term (1-3 days each)

6. **Add dark mode overrides for `btn-tertiary`, `btn-danger`, `btn--transparent`** in `_buttons.scss`.
7. **Add dark mode conditionals to chart components** — Use `getDarkMode()` to swap axis/grid colours.
8. **Fix feature pipeline status dark mode** — Add `.dark` overrides to `_feature-pipeline-status.scss`.
9. **Add dark mode checkbox/switch focus states** — Complete the missing `:focus`, `:hover`, `:disabled` dark overrides.
10. **Standardise off-grid spacing** — Bulk replace 5px→4px, 6px→4px or 8px, formalise 12px as `$spacer * 0.75`.

### Long-Term (design system roadmap)

11. **Add general-purpose font-weight tokens** — `$font-weight-regular: 400`, `$font-weight-medium: 500`, `$font-weight-semibold: 600`, `$font-weight-bold: 700`.
12. **Refactor Icon.tsx** — Extract inline SVGs to individual files, integrate `svg/` components, migrate IonIcon usage.
13. **Consolidate confirmation modals** — Create a single configurable `ConfirmModal` replacing 13+ near-identical implementations.
14. **Migrate modal API** — Replace global `openModal`/`closeModal` with React context-based modal manager.
15. **Extract shared dropdown primitive** — Replace 4 independent dropdown/popover implementations.
16. **Unify alert components** — Single `Alert` component with `variant` prop replacing `ErrorMessage`, `SuccessMessage`, `InfoMessage`, `WarningMessage`.
17. **Convert legacy components** — `Flex.js`, `Column.js`, `Panel.tsx` to TypeScript FCs. Remove `@material-ui/core` dependency from `AccordionCard`.
18. **Establish Storybook** — Document all base components with visual regression testing.
