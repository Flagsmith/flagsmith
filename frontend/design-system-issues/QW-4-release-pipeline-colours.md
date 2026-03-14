---
title: "Release pipeline hardcoded colours"
labels: ["design-system", "quick-win", "dark-mode", "colours"]
---

## Problem

Release pipeline components use raw hex values for status indicator colours instead of theme tokens. These colours do not adapt to dark mode and are not tied to the design system token layer, making future theming changes harder to propagate.

## Files

- `web/components/release-pipelines/ReleasePipelinesList.tsx:169` — `color: isPublished ? '#6837FC' : '#9DA4AE'`
- `web/components/release-pipelines/ReleasePipelineDetail.tsx:106` — `color: isPublished ? '#6837FC' : '#9DA4AE'` (same pattern)
- `web/components/release-pipelines/StageCard.tsx:8` — `bg-white` Bootstrap class hardcoded, no dark mode equivalent applied

## Proposed Fix

Replace hardcoded hex values with tokens from `common/theme`:

```tsx
import { colorBrandPrimary, colorTextTertiary } from 'common/theme'

// Before
color: isPublished ? '#6837FC' : '#9DA4AE'

// After
color: isPublished ? colorBrandPrimary : colorTextTertiary
```

For `StageCard.tsx`, replace the hardcoded `bg-white` class with the appropriate themed background token (e.g. a CSS custom property via `var(--color-bg-level-1)`), consistent with how other card components handle their background in dark mode.

## Acceptance Criteria

- [ ] Published/unpublished status colours in `ReleasePipelinesList` and `ReleasePipelineDetail` use theme tokens
- [ ] `StageCard` background renders correctly in both light and dark mode
- [ ] No hardcoded hex colour values remain in release pipeline components
- [ ] Visual appearance in light mode is unchanged

## Storybook Validation

Design System / Release Pipelines — verify status indicators and card backgrounds in both light and dark mode.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
