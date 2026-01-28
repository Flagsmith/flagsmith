# E2E Enterprise Test Runner

Run enterprise E2E tests (tagged with @enterprise), analyze failures, fix them, and re-run until all pass.

## Arguments

- `$ARGUMENTS` = "" → Run tests once (default)
- `$ARGUMENTS` = "5" → Run tests 5 times, stopping on first failure

## CRITICAL: Read Context First

**You MUST read `.claude/context/e2e.md` before proceeding.** It contains essential configuration, failure analysis workflows, and fix patterns.

## Run Command

```bash
cd frontend
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep @enterprise --quiet
```

## Re-running Failed Enterprise Tests

When re-running specific failed tests, include the grep flag:
```bash
cd frontend
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/specific-test.pw.ts --grep @enterprise
```

## Workflow

1. Run tests (one iteration at a time if multiple requested)
2. On failure: follow the failure analysis workflow in context/e2e.md
3. Report results
