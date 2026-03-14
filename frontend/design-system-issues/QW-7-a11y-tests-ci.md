---
title: "POC: Evaluate wiring accessibility E2E tests into CI"
labels: ["design-system", "quick-win", "accessibility", "spike"]
---

## Objective

Evaluate the feasibility of integrating the existing axe-core/Playwright accessibility tests into the CI pipeline. This is a spike/POC — not an implementation commitment.

## Context

6 axe-core/Playwright accessibility E2E tests exist in the repository (`e2e/tests/accessibility-tests.pw.ts`) but are not included in the CI pipeline. Before committing to full integration, we need to understand:

1. **CI impact** — How much time do the a11y tests add to the pipeline?
2. **Noise level** — How many existing violations surface? Are they actionable or overwhelming?
3. **Severity filtering** — Can we configure axe to fail only on `critical`/`serious` violations?
4. **Infrastructure** — Do the tests need Docker services running? What's the dependency footprint?

## Files to Investigate

- `e2e/tests/accessibility-tests.pw.ts` — existing axe-core tests (6 tests)
- `e2e/helpers/accessibility.playwright.ts` — `checkA11y()` helper
- `.github/workflows/` — existing CI workflow files
- `e2e/playwright.config.ts` — test configuration

## POC Tasks

- [ ] Run the a11y tests locally and document pass/fail results
- [ ] Measure execution time
- [ ] List all current violations by severity level
- [ ] Draft a CI workflow addition (without merging)
- [ ] Document findings and recommendation (proceed / defer / adjust scope)

## Success Criteria

A short write-up answering: Should we wire these tests into CI now, and if so, with what configuration?

## Dependencies

None — tests already exist and pass locally.

---
Part of the Design System Audit (#6606)
