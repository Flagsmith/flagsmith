---
title: "Convert remaining .js components to TypeScript"
labels: ["design-system", "large-refactor", "tech-debt"]
status: DRAFT
---

## Problem

50 `.js` files remain in `web/components/` alongside their `.tsx` counterparts.
Many are class components using `propTypes`, `module.exports`, and the global
component registry (`window.Button`, `window.Row`, etc.).

### Specific issues

1. **3 confirmed duplicate coexisting files** — both a `.js` and `.tsx` version
   exist for the same component, creating ambiguity about which is actually used:
   - `web/components/modals/CreateWebhook.js` + `CreateWebhook.tsx`
   - `web/components/ErrorMessage.js` + `messages/ErrorMessage.tsx`
   - `web/components/SuccessMessage.js` + `messages/SuccessMessage.tsx`

2. **Class components with propTypes** — files like `Flex.js`, `Column.js`,
   `Input.js`, `InputGroup.js`, `Tabs.js`, `Payment.js`, `CreateProject.js` use
   the class component pattern with `propTypes` instead of TypeScript interfaces.

3. **`module.exports` usage** — older files use CommonJS exports rather than ES
   module syntax, preventing proper static analysis and tree-shaking.

4. **Global registry dependency** — many `.js` files rely on `window.Button`,
   `window.Row`, etc. from `project-components.js` instead of explicit imports
   (see LR-9). These cannot be converted to `.tsx` without first adding imports.

### Full list of .js files in web/components/

**Top level (30 files):**
`AdminAPIKeys.js`, `App.js`, `AsideProjectButton.js`, `AsideTitleLink.js`,
`Blocked.js`, `CodeHelp.js`, `Collapsible.js`, `CompareEnvironments.js`,
`CompareFeatures.js`, `ErrorMessage.js`, `FlagOwnerGroups.js`, `FlagOwners.js`,
`FlagSelect.js`, `Headway.js`, `Highlight.js`, `HistoryIcon.js`,
`Maintenance.js`, `OrganisationSelect.js`, `Paging.js`,
`PasswordRequirements.js`, `ProjectSelect.js`, `RebrandBanner.js`,
`SamlForm.js`, `SegmentOverrides.js`, `ServerSideSDKKeys.js`,
`SuccessMessage.js`, `Token.js`, `TryIt.js`, `TwoFactor.js`, `ValueEditor.js`

**Base components (5 files):**
`base/forms/Input.js`, `base/forms/InputGroup.js`, `base/forms/Tabs.js`,
`base/grid/Column.js`, `base/grid/Flex.js`

**Modals (5 files):**
`modals/CreateProject.js`, `modals/CreateWebhook.js`, `modals/Payment.js`,
`modals/create-experiment/index.js`, `modals/create-feature/index.js`

**Pages (7 files):**
`pages/AccountSettingsPage.js`, `pages/ComingSoonPage.js`, `pages/ComparePage.js`,
`pages/ConfirmEmailPage.js`, `pages/InvitePage.js`, `pages/NotFoundErrorPage.js`,
`pages/PasswordResetPage.js`, `pages/UserIdPage.js`

**Other (3 files):**
`SimpleTwoFactor/index.js`, `SimpleTwoFactor/prompt.js`

## Files

- All 50 `.js` files listed above in `web/components/`
- `web/project/project-components.js` — global registry (see LR-9)

## Proposed Fix

### Phase 1 — Delete confirmed duplicates

Delete the 3 `.js` files that have `.tsx` replacements already in use:
- Delete `web/components/modals/CreateWebhook.js` (keep `CreateWebhook.tsx`)
- Delete `web/components/ErrorMessage.js` (keep `messages/ErrorMessage.tsx`)
- Delete `web/components/SuccessMessage.js` (keep `messages/SuccessMessage.tsx`)

Verify no import path resolves to the deleted `.js` file.

### Phase 2 — Convert simple functional components

Start with files that are already functional components or trivial class
components. For each file:
1. Rename `.js` → `.tsx`
2. Replace `propTypes` with a TypeScript `interface` or `type`
3. Replace `module.exports` with `export default`
4. Add explicit imports for any globally-registered components
5. Run `npx eslint --fix <file>` and `npm run typecheck`

### Phase 3 — Convert class components

For files using `class extends Component`:
1. Convert to functional component with hooks where straightforward
2. If the class component has complex lifecycle methods, convert to hooks
   (`useEffect`, `useCallback`, etc.)
3. Add proper TypeScript interfaces for props and state

### Phase 4 — Convert page and modal components

These tend to be larger and more complex. Convert after the simpler components
are done, as patterns established in Phase 2-3 can be reused.

## Acceptance Criteria

- [ ] Zero `.js` files remain in `web/components/`
- [ ] No `propTypes` imports remain in converted files
- [ ] No `module.exports` usage remains in converted files
- [ ] All converted files have TypeScript interfaces for their props
- [ ] `npm run typecheck` passes with no new errors
- [ ] `npm run build` completes successfully
- [ ] No duplicate `.js` + `.tsx` files exist for the same component

## Dependencies

- **LR-9** (Remove global component registry) should be completed first — without
  it, `.js` files that use `window.Button` etc. cannot be converted because
  TypeScript will flag the missing imports
- Related to **LR-3** (Modal system migration) — the 3 legacy JS modals
  (`CreateProject.js`, `CreateWebhook.js`, `Payment.js`) will be addressed there
- Enables better `npm run typecheck` coverage across the codebase

---
Part of the Design System Audit (#6606)
