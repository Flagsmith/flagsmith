---
title: "Decouple Button from Redux store (dead feature prop)"
labels: ["design-system", "quick-win", "storybook", "technical-debt"]
issue: https://github.com/Flagsmith/flagsmith/issues/6866
---

## Problem

`Button.tsx` imports `Utils` from `common/utils/utils`, which pulls in the entire Redux store + Flux store + CommonJS `_data.js` chain **at import time**. This blocks Storybook from importing Button or any of the 150+ components that depend on it.

The `Utils` import exists solely for `Utils.getPlansPermission(feature)` — but **zero consumers pass the `feature` prop to Button**. It's dead code.

Current Storybook Button stories use raw `<button>` HTML elements with CSS classes (visual replicas), not the real `<Button>` component.

## Files

- `web/components/base/forms/Button.tsx` — remove `Utils`, `PaidFeature`, `PlanBasedBanner` imports and dead `feature` prop logic
- `stories/Buttons.stories.tsx` — replace raw `<button>` elements with real `<Button>` component

## Proposed Fix

### Button.tsx

1. Remove `import Utils, { PaidFeature } from 'common/utils/utils'`
2. Remove `import PlanBasedBanner from 'components/PlanBasedAccess'`
3. Remove `feature` from `ButtonType` props interface
4. Remove `feature` from destructured props
5. Remove `const hasPlan = feature ? Utils.getPlansPermission(feature) : true`
6. Simplify render: remove `hasPlan` conditional branching — always render standard button/anchor
7. Keep the `href` anchor branch (used for link-style buttons), just remove plan-gating logic within it

### Storybook stories

1. Import the real `Button` component instead of using raw `<button>` elements
2. Replace `<button className="btn btn-primary">` with `<Button theme="primary">`
3. Add an Interactive story with Storybook args/controls
4. Keep the dark mode gap documentation (valuable audit evidence)

## Verification

```bash
# Confirm no consumers pass `feature` to Button
grep -r 'feature=' --include='*.tsx' --include='*.js' | grep '<Button'

# Type check
npm run typecheck

# Lint
npx eslint --fix web/components/base/forms/Button.tsx stories/Buttons.stories.tsx
```

## Acceptance Criteria

- [ ] `Button.tsx` has no imports from `common/utils/utils` or `components/PlanBasedAccess`
- [ ] `ButtonType` no longer includes `feature` prop
- [ ] `npm run typecheck` passes
- [ ] Storybook Button stories render the real `<Button>` component
- [ ] All existing Button functionality (href, icons, themes, sizes, disabled) works unchanged
