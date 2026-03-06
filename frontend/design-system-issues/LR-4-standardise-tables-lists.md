---
title: "Standardise table/list components"
labels: ["design-system", "large-refactor"]
---

## Problem

There is no unified table or list component system. Each feature area builds its own ad hoc implementation, resulting in visual inconsistency and duplicated logic:

- 9 different `TableFilter*` components
- 5+ different `*Row` components (`FeatureRow`, `ProjectFeatureRow`, `FeatureOverrideRow`, `OrganisationUsersTableRow`, etc.)
- 5+ different `*List` components

There is no shared abstraction for sorting, filtering, pagination, empty states, or loading skeletons. Changes to table behaviour (e.g. keyboard navigation, row hover, selection) must be made in every implementation separately.

## Files

- `web/components/` — `TableFilter*`, `*Row`, and `*List` components scattered across feature directories

## Proposed Fix

Create a composable `Table` / `List` component system with standardised sub-components:

- `Table`, `Table.Header`, `Table.Row`, `Table.Cell`
- `List`, `List.Item`
- Shared empty state and loading skeleton slots

Migrate feature areas one at a time. Do not attempt a single large migration — migrate the simplest feature area first to validate the API, then proceed.

## Acceptance Criteria

- [ ] Shared `Table` and `List` components exist with documented sub-component API
- [ ] At least one feature area is fully migrated as a reference implementation
- [ ] Remaining feature areas are migrated incrementally (tracked in sub-tasks)
- [ ] Visual output is identical before and after migration for each area
- [ ] Empty state and loading state are handled consistently

## Storybook Validation

- `Design System/Table` — verify all Table variants and states
- `Design System/List` — verify all List variants and states

## Dependencies

None.

---
Part of the Design System Audit (#6606)
