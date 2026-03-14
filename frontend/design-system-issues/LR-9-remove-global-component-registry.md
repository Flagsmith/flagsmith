---
title: "Remove global component registry in project-components.js"
labels: ["design-system", "large-refactor", "tech-debt"]
status: DRAFT
---

## Problem

`web/project/project-components.js` attaches ~15 components and providers to
`window` (and `global`), making them available implicitly across the entire
codebase without any import statement:

```js
window.Button = Button
window.Row = Row
window.Select = Select
window.Input = Input
window.InputGroup = InputGroup
window.FormGroup = FormGroup
window.Panel = Panel
window.PanelSearch = PanelSearch
window.CodeHelp = CodeHelp
window.Loader = class extends PureComponent { ... }  // defined inline
window.Tooltip = Tooltip
global.ToggleChip = ToggleChip
global.Select = class extends PureComponent { ... }  // wrapper defined inline
```

This was a common pre-module-era shortcut, but it causes several concrete
problems today:

- **TypeScript blindness** — the TS compiler has no knowledge of `window.Button`
  so any `.js` file that uses it cannot be migrated to `.tsx` without first
  adding an explicit import. This is the root blocker for completing LR-5.
- **ESLint no-undef suppression** — usages like bare `Button` or `Row` in `.js`
  files would trigger `no-undef` if the global polyfill weren't there. This
  masks real missing-import bugs (e.g. `Button` in `SuccessMessage.js`).
- **Tree-shaking defeated** — bundlers cannot eliminate unused globals. Every
  component in `project-components.js` ships in every bundle regardless of
  whether it's used on that page.
- **Storybook incompatibility** — the global registry is not set up in the
  Storybook environment, so `.js` components that rely on `window.Button` etc.
  cannot be rendered in isolation without special mocking.
- **Hidden coupling** — nothing in a consuming file signals its dependency on
  `project-components.js` being loaded first. This makes the dependency graph
  invisible to tooling and to new contributors.

## Files

- `web/project/project-components.js` — the registry itself
- All `.js` components that use globals without importing them (see LR-5 for
  the list; examples include `SuccessMessage.js`, `CodeHelp.js`, `Payment.js`)

## Proposed Fix

### Step 1 — Audit all global usages

```bash
grep -rn "window\.Button\|window\.Row\|window\.Select\|window\.Input\|window\.Panel\|window\.Loader\|window\.Tooltip\|window\.Paging\|window\.FormGroup\|window\.CodeHelp\|window\.PanelSearch\|global\.ToggleChip\|global\.Select" web/ common/ --include='*.js' --include='*.ts' --include='*.tsx'
```

Also grep for bare usages (no `window.` prefix) in `.js` files:

```bash
grep -rn "\bButton\b\|\bRow\b\|\bSelect\b\|\bLoader\b" web/components --include='*.js'
```

### Step 2 — Add explicit imports to each consuming file

For each `.js` file that uses a global component, add the correct import.
Example for `SuccessMessage.js`:

```js
// Before — relies on window.Button
<Button className='btn my-2' onClick={this.handleOpenNewWindow}>

// After — explicit import at top of file
import Button from 'components/base/forms/Button'
```

### Step 3 — Remove window/global assignments from project-components.js

Once all call sites have explicit imports, remove the `window.*` and `global.*`
assignments one by one, verifying the build passes after each removal.

### Step 4 — Delete or repurpose project-components.js

If the file's only remaining purpose is the `Loader` and `Select` wrapper
class components defined inline, extract those to proper files and delete
`project-components.js`. If it still serves as a bundle entry point, strip it
down to only what's necessary and add a comment explaining its role.

## Acceptance Criteria

- [ ] No `window.*` or `global.*` component assignments remain in
      `project-components.js`
- [ ] Every component previously registered globally has an explicit import in
      each file that uses it
- [ ] `npm run typecheck` passes with no new errors
- [ ] `npm run build` completes and bundle size is not increased
- [ ] All `.js` files that consumed globals are candidates for LR-5 (TS migration)
- [ ] `Loader` and `Select` wrapper are extracted to standalone files if kept

## Storybook Validation

After this change, the `.js` components should be renderable in Storybook
without global mocking. Verify that any story that imports a component
previously relying on globals renders correctly.

## Dependencies

- Prerequisite for **LR-5** (Remove legacy JS class components) — globals must
  be replaced with explicit imports before `.js` files can be converted to
  `.tsx`
- Related to **LR-3** (Modal system migration) — that issue covers a separate
  but similar global pattern (`openModal`, `openConfirm` on `window`)

---
Part of the Design System Audit (#6606)
