---
title: "Remove legacy JS class components"
labels: ["design-system", "large-refactor"]
---

## Problem

Several components remain as `.js` class components. These cannot be type-checked, do not support modern React patterns (hooks, context), and block TypeScript strictness improvements across the codebase. One file (`CreateWebhook.js`) coexists with a `.tsx` version of the same component, creating an ambiguous import situation.

## Files

- `web/components/base/forms/Input.js` — legacy class component
- `web/components/base/forms/InputGroup.js` — legacy class component
- `web/components/modals/CreateProject.js` — legacy class component
- `web/components/modals/CreateWebhook.js` — legacy duplicate; `.tsx` version exists
- `web/components/modals/Payment.js` — legacy class component
- `web/components/Flex.js` — layout primitive, legacy class component
- `web/components/Column.js` — layout primitive, legacy class component

## Proposed Fix

Convert each file to a TypeScript functional component (`.tsx`). Delete `CreateWebhook.js` — the `.tsx` version is the canonical implementation. Verify all import paths resolve to the `.tsx` file after deletion.

## Acceptance Criteria

- [ ] All listed `.js` files are converted to `.tsx` functional components
- [ ] `CreateWebhook.js` is deleted; all imports resolve to the `.tsx` version
- [ ] `npm run typecheck` passes with no new errors
- [ ] `npm run lint` passes
- [ ] No runtime regressions in the converted components

## Storybook Validation

Verify that `Input`, `InputGroup`, `Flex`, and `Column` stories (if they exist) still render correctly after conversion.

## Dependencies

None — each file can be converted independently.

---
Part of the Design System Audit (#6606)
