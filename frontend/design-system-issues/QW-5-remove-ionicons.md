---
title: "Remove unused ionicons dependency"
labels: ["design-system", "quick-win"]
---

## Problem

The packages `ionicons` (v7.2.1) and `@ionic/react` (v7.5.3) are listed in `package.json` but are not imported or used anywhere in the codebase. These packages add unnecessary weight to the dependency tree and could be a source of supply chain risk.

## Files

- `package.json` — lists `ionicons` and `@ionic/react` as dependencies
- `package-lock.json` — will need to be updated after removal

## Proposed Fix

Uninstall both packages:

```bash
npm uninstall ionicons @ionic/react
```

Verify no imports remain after removal:

```bash
grep -r 'ionicons\|@ionic/react' web/ common/ --include='*.ts' --include='*.tsx' --include='*.js'
```

## Acceptance Criteria

- [ ] `ionicons` and `@ionic/react` are removed from `package.json` and `package-lock.json`
- [ ] No import errors appear after removal
- [ ] `npm run build` completes successfully
- [ ] Bundle size is reduced (confirm with a before/after comparison if possible)

## Storybook Validation

Not applicable — this is a dependency cleanup task with no UI impact.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
