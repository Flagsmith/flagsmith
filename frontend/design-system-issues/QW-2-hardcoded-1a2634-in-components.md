---
title: "Remove hardcoded #1A2634 from components outside Icon.tsx"
labels: ["design-system", "quick-win", "dark-mode"]
---

## Problem

Several components outside `Icon.tsx` pass `#1A2634` directly as a `fill` prop to icons or as a `tick` fill to chart elements. These values are invisible in dark mode and bypass the theme system entirely.

## Files

- `web/components/StatItem.tsx:43` — `fill='#1A2634'`
- `web/components/Switch.tsx:57` — `fill={checked ? '#656D7B' : '#1A2634'}`
- `web/components/DateSelect.tsx:136` — `fill={isOpen ? '#1A2634' : '#9DA4AE'}`
- `web/components/pages/ScheduledChangesPage.tsx:126` — `fill={'#1A2634'}`
- `web/components/organisation-settings/usage/OrganisationUsage.container.tsx:63` — `tick={{ fill: '#1A2634' }}`
- `web/components/organisation-settings/usage/components/SingleSDKLabelsChart.tsx:62` — `tick={{ fill: '#1A2634' }}`

Already correct (no action needed):

- `web/components/CompareIdentities.tsx:214` — uses `getDarkMode()` conditional
- `web/components/RuleConditionValueInput.tsx:150` — uses `getDarkMode()` conditional

## Proposed Fix

- For icon `fill` props: after QW-1 ships, remove the explicit `fill` prop entirely so icons inherit `currentColor` from CSS context.
- For cases where a conditional colour is needed (e.g. `Switch.tsx`), replace with appropriate theme tokens.
- For chart tick fills: import `colorTextStandard` from `common/theme` and use it instead of the hardcoded hex.

```tsx
// Before
tick={{ fill: '#1A2634' }}

// After
import { colorTextStandard } from 'common/theme'
tick={{ fill: colorTextStandard }}
```

## Acceptance Criteria

- [ ] No hardcoded `#1A2634` fill values remain in any component outside `Icon.tsx`
- [ ] All affected components render correctly in both light and dark mode
- [ ] Chart tick labels are legible in dark mode
- [ ] Theme token usage is consistent with the rest of the codebase

## Storybook Validation

Design System / Dark Mode Issues / Hardcoded Colours In Components — verify each listed component renders correctly on both light and dark backgrounds.

## Dependencies

Depends on QW-1 (Icon.tsx currentColor fix) being merged first, so that removing explicit `fill` props does not cause regressions.

---
Part of the Design System Audit (#6606)
