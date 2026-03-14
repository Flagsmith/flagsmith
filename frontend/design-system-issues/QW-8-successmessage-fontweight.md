---
title: "Fix invalid fontWeight and consolidate SuccessMessage"
labels: ["design-system", "quick-win", "bug"]
issue: https://github.com/Flagsmith/flagsmith/issues/6872
pr: https://github.com/Flagsmith/flagsmith/pull/6873
---

## Problem

`SuccessMessage.tsx` line 44 sets `fontWeight: 'semi-bold'` as an inline style. This is not a valid CSS `font-weight` value — browsers silently ignore it, so the title renders with default `font-weight: 400` instead of the intended `600`.

## Scope (updated to match PR #6873)

The PR expanded beyond the original fontWeight fix:

| Change | Detail |
|--------|--------|
| Fix fontWeight | `style={{ fontWeight: 'semi-bold' }}` → `className='fw-semibold'` (Bootstrap utility) |
| Delete legacy component | `web/components/SuccessMessage.js` deleted (class component, 47 lines, same bug) |
| Update imports | `AdminAPIKeys.js`: `./SuccessMessage` → `./messages/SuccessMessage` |
| Update imports | `FeatureImport.tsx`: `components/SuccessMessage` → `components/messages/SuccessMessage` |

This partially covers QW-5 (duplicate legacy component removal). The remaining ErrorMessage.js consolidation is tracked separately in QW-5.

## Files

- `web/components/messages/SuccessMessage.tsx` — fontWeight fix
- `web/components/SuccessMessage.js` — **deleted**
- `web/components/AdminAPIKeys.js` — import path updated
- `web/components/import-export/FeatureImport.tsx` — import path updated

## Acceptance Criteria

- [x] `fontWeight: 'semi-bold'` replaced with Bootstrap `fw-semibold` class
- [x] Legacy `SuccessMessage.js` deleted
- [x] All import paths updated to `components/messages/SuccessMessage`
- [ ] `npm run typecheck` passes
- [ ] Success message title visibly renders in semi-bold weight

---
Part of the Design System Audit (#6606)
