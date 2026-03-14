---
title: "Consolidate 6 identical ConfirmRemove* modals"
labels: ["design-system", "medium-effort"]
---

## Problem

6 deletion confirmation modals follow the exact same "type the name to confirm" pattern but are implemented as separate files with duplicated logic. This results in approximately 500 lines of redundant code and makes future changes to the pattern require 6 separate edits.

## Files

- `web/components/modals/ConfirmRemoveFeature.tsx` — duplicate confirmation modal
- `web/components/modals/ConfirmRemoveSegment.tsx` — duplicate confirmation modal
- `web/components/modals/ConfirmRemoveProject.tsx` — duplicate confirmation modal
- `web/components/modals/ConfirmRemoveOrganisation.tsx` — duplicate confirmation modal
- `web/components/modals/ConfirmRemoveEnvironment.tsx` — duplicate confirmation modal
- `web/components/modals/ConfirmRemoveWebhook.tsx` — duplicate confirmation modal

## Proposed Fix

Create a single `ConfirmRemoveModal` component with `entityType`, `entityName`, and `onConfirm` props. Replace all 6 existing files with usages of the new unified component.

Example API:

```tsx
<ConfirmRemoveModal
  entityType="feature"
  entityName={feature.name}
  onConfirm={handleDelete}
/>
```

Delete the 6 original files once all call sites are updated.

## Acceptance Criteria

- [ ] Single reusable `ConfirmRemoveModal` component exists
- [ ] All 6 use cases (feature, segment, project, organisation, environment, webhook) work identically to before
- [ ] No visual regression across any of the 6 deletion flows
- [ ] Approximately 500 lines of duplicated code removed
- [ ] No existing tests broken

## Storybook Validation

Not applicable — this is a refactor of modal logic with no change to visual output. Manual testing of each deletion flow is sufficient.

## Dependencies

None.

---
Part of the Design System Audit (#6606)
