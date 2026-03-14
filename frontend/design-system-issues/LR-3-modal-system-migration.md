---
title: "Modal system — migrate from global imperative API"
labels: ["design-system", "large-refactor"]
---

## Problem

The modal system exposes `openModal()`, `openModal2()`, and `openConfirm()` as global functions attached to `window`. This approach has three critical problems:

1. **Deprecated React APIs** — the implementation uses `ReactDOM.render` and `ReactDOM.unmountComponentAtNode`, both of which were removed in React 18. The app is currently blocked from upgrading React without addressing this.
2. **`openModal2` exists for stacking modals** — its existence is acknowledged in the code as a pattern to avoid, yet it remains in use.
3. **No React context** — modals rendered outside the React tree cannot access context (theme, auth, feature flags, etc.) without prop-drilling workarounds.

## Files

- `web/components/modals/` — modal implementations calling the global API
- `common/code/modalService.ts` (or equivalent) — `openModal`, `openModal2`, `openConfirm` definitions
- All callsites of `openModal()`, `openModal2()`, `openConfirm()` across the codebase

## Proposed Fix

Migrate to a React context-based modal manager:

- Introduce a `ModalProvider` at the app root
- Expose a `useModal()` hook that replaces all global function calls
- Support modal stacking natively within the context (eliminating the need for `openModal2`)
- Modals rendered inside the React tree gain access to all context providers

## Acceptance Criteria

- [ ] `openModal`, `openModal2`, and `openConfirm` are removed from `window`
- [ ] All modal invocations use the `useModal()` hook
- [ ] Modal stacking works without `openModal2`
- [ ] No usage of `ReactDOM.render` or `ReactDOM.unmountComponentAtNode` remains
- [ ] The app is compatible with React 18 after this change
- [ ] Existing modal behaviour (open, close, confirm, nested) is preserved

## Storybook Validation

Not directly applicable — validate via manual testing and E2E tests covering modal open/close/confirm flows.

## Dependencies

None — this is a blocker for React 18 compatibility.

---
Part of the Design System Audit (#6606)
