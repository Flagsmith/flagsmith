---
title: "Wire accessibility E2E tests into CI"
labels: ["design-system", "quick-win", "accessibility"]
---

## Problem

6 axe-core/Playwright accessibility E2E tests exist in the repository but are not included in the CI pipeline. This means contrast ratio regressions and other accessibility violations can be merged to `main` without being caught automatically.

## Files

- `e2e/tests/accessibility-tests.pw.ts` — existing axe-core tests (6 tests)
- `e2e/helpers/accessibility.playwright.ts` — `checkA11y()` helper used by the tests
- CI config (GitHub Actions workflow file) — needs an accessibility test job added

## Proposed Fix

Add the accessibility tests to the existing Playwright CI job. The tests should be configured to fail only on `critical` and `serious` axe violations, not `moderate` or `minor`, to avoid excessive noise while still blocking regressions.

Example configuration in the workflow:

```yaml
- name: Run accessibility tests
  run: npm run test -- e2e/tests/accessibility-tests.pw.ts
  env:
    E2E_RETRIES: 1
```

If the existing CI job runs tests by tag, ensure the accessibility tests carry an appropriate tag (e.g. `@a11y`) so they can be targeted or excluded independently.

## Acceptance Criteria

- [ ] CI runs the accessibility tests on every pull request
- [ ] Tests fail on `critical` and `serious` axe violations
- [ ] Contrast ratio regressions block merging
- [ ] CI job name and step are clearly labelled as accessibility tests
- [ ] Existing test run time is not significantly impacted (accessibility tests are fast)

## Storybook Validation

Not applicable — this is a CI configuration task.

## Dependencies

None — tests already exist and pass locally.

---
Part of the Design System Audit (#6606)
