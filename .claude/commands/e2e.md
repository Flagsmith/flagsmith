# E2E Test Runner with Auto-Fix

Run E2E tests with the following configuration:
- `SKIP_BUNDLE=1` - Skip bundle build for faster iteration
- `E2E_CONCURRENCY=20` - High concurrency for speed
- `--grep-invert @enterprise` - Only run OSS tests
- `--quiet` - Minimal output

## Context

- Test files location: `frontend/e2e/tests/*.pw.ts`
- Test results: `frontend/e2e/test-results/results.json`
- Tests use Playwright with Firefox
- The retry logic is built into the test runner (via `run-with-retry.ts`)
- Tests run against a local Docker environment (API + DB)

## Workflow

1. **Run tests** from the frontend directory:
   ```bash
   cd frontend
   SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep-invert @enterprise --quiet
   ```

2. **If ANY tests fail (even after automatic retries):**

   a. Parse the test output and `e2e/test-results/results.json` to identify failures

   b. For EACH failed test:
      - Read the test file
      - Read the error message and stack trace
      - Analyze the root cause
      - **Attempt to fix the issue** if it's one of these:
        - Missing `data-test` attribute → Add it to the component
        - Selector changed → Update the test to use the new selector
        - Missing wait → Add appropriate `waitFor*` calls
        - Race condition → Add network waits, increase timeouts, or use more specific waits
        - Flaky element interaction → Add `scrollIntoView` or `waitForVisible` before clicking

   c. **After making fixes**, re-run ONLY the failed tests:
      ```bash
      cd frontend
      SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts tests/invite-test.pw.ts
      ```
      - Use concurrency=1 to avoid race conditions
      - Only run the specific test files that failed

   d. **If tests still fail after fixes:**
      - Try a second round of fixes if the error changed
      - Otherwise, report the issue with details on what was attempted

3. **Report final results:**
   - List which tests passed/failed
   - Document any fixes that were applied
   - For unfixable issues, explain why and suggest manual investigation

## Important Notes

- **DO NOT** just report that retries passed - if tests failed initially, investigate and fix the root cause
- **DO** modify test files to fix timing issues, missing waits, or broken selectors
- **DO** add `data-test` attributes to components if they're missing
- **DON'T** modify test assertions or business logic unless the test is clearly wrong
- If the failure is in application code (not test code), report it as a bug but don't try to fix it
- Always explain what fixes you're attempting and why
- Test files are in TypeScript and use the `helpers.playwright.ts` helper functions
- The built-in retry mechanism is a safety net, not a substitute for fixing flaky tests
