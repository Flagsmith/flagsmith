# Visual Regression Test Runner

Run local visual regression tests by capturing baselines from main on this machine, then comparing against the current branch. Both runs use the same OS and browser, so diffs reflect actual style changes rather than platform rendering differences.

## Prerequisites

- Docker running with Flagsmith services on localhost:8000

## Workflow

1. Capture local baselines from main (stashes changes, checks out main, runs E2E, switches back):

```bash
npm run test:visual:baselines
```

2. Run E2E tests on the current branch with visual regression screenshot capture:

```bash
VISUAL_REGRESSION=1 npm run test
```

3. Compare captured screenshots against local baselines:

```bash
npm run test:visual:compare
```

4. If there are failures, open the HTML report for visual diff inspection:

```bash
npm run test:visual:report
```

5. Report results: how many comparisons passed/failed, and whether failures are style/layout regressions or data differences.
