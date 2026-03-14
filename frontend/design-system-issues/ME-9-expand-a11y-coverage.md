---
title: "Expand accessibility E2E coverage to all key pages"
labels: ["design-system", "medium-effort", "accessibility"]
---

## Problem

The current axe-core accessibility test suite (added in #6562) only covers 6 scenarios:

- Features list (light mode)
- Features list (dark mode)
- Project Settings
- Environment Switcher
- Create Feature modal (light mode)
- Create Feature modal (dark mode)

The following key pages have no accessibility coverage at all:

- Segments
- Audit Log
- Integrations
- Users & Permissions
- Organisation Settings
- Identities
- Release Pipelines
- Change Requests

## Files

- `e2e/tests/accessibility-tests.pw.ts` — existing test file to extend with additional page tests

## Proposed Fix

Add light and dark mode contrast tests for each missing page following the existing pattern in `e2e/tests/accessibility-tests.pw.ts`. Each page should have at minimum:

1. A test that navigates to the page in light mode and runs `checkA11y()`
2. A test that toggles dark mode and runs `checkA11y()`

Use the same axe-core configuration and violation thresholds already established in the existing tests.

## Acceptance Criteria

- [ ] Segments page covered in light and dark mode
- [ ] Audit Log page covered in light and dark mode
- [ ] Integrations page covered in light and dark mode
- [ ] Users & Permissions page covered in light and dark mode
- [ ] Organisation Settings page covered in light and dark mode
- [ ] Identities page covered in light and dark mode
- [ ] Release Pipelines page covered in light and dark mode
- [ ] Change Requests page covered in light and dark mode
- [ ] All new tests pass in CI
- [ ] No existing tests regressed

## Storybook Validation

Not applicable — these are E2E page-level tests, not Storybook component tests.

## Dependencies

ME-8 (@storybook/addon-a11y) is complementary but independent — this ticket covers E2E coverage, ME-8 covers component-level coverage.

---
Part of the Design System Audit (#6606)
