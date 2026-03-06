---
title: "Chart axis labels invisible in dark mode"
labels: ["design-system", "quick-win", "dark-mode"]
---

## Problem

Recharts `XAxis` and `YAxis` components across multiple chart files use hardcoded hex values for `tick` fill colours. In dark mode, these tick labels become invisible because the hardcoded colours do not adapt to the background.

## Files

- `web/components/organisation-settings/usage/OrganisationUsage.container.tsx` — lines 56, 63
- `web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx` — lines 53, 62
- `web/components/pages/admin-dashboard/components/UsageTrendsChart.tsx`
- `web/components/feature-page/FeatureNavTab/FeatureAnalytics.tsx`

## Proposed Fix

Import theme colour tokens and use them in place of hardcoded hex values:

```tsx
import { colorTextStandard, colorTextSecondary } from 'common/theme'

// Before
<XAxis tick={{ fill: '#1A2634' }} />
<YAxis tick={{ fill: '#9DA4AE' }} />

// After
<XAxis tick={{ fill: colorTextStandard }} />
<YAxis tick={{ fill: colorTextSecondary }} />
```

The tokens from `common/theme` already resolve to the correct value for the active colour mode, so no additional dark mode conditionals are needed.

## Acceptance Criteria

- [ ] All chart axis labels are legible in both light and dark mode
- [ ] No hardcoded hex colour values remain in chart tick configurations
- [ ] Token usage matches `colorTextStandard` and `colorTextSecondary` as appropriate to the label hierarchy

## Storybook Validation

Not directly applicable to Recharts charts, but manual verification on the Organisation Usage page and Feature Analytics page in dark mode will confirm the fix.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
