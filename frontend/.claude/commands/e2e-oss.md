# E2E OSS Test Runner

Run OSS (non-enterprise) E2E tests and report results.

## Arguments

- `$ARGUMENTS` = "" → Run tests once (default)
- `$ARGUMENTS` = "5" → Run tests 5 times, stopping on first failure

## CRITICAL: Read Context First

**You MUST read `.claude/context/e2e.md` before proceeding.** It contains essential configuration, failure analysis workflows, and fix patterns.

## Run Command

```bash
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep @oss --quiet
```

## Workflow

1. Run tests (one iteration at a time if multiple requested)
2. On failure: follow the failure analysis workflow in context/e2e.md
3. Report results
