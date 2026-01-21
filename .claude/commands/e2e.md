# E2E Test Runner with Auto-Fix

Run E2E tests with the following configuration:
- `SKIP_BUNDLE=1` - Skip bundle build for faster iteration
- `E2E_CONCURRENCY=20` - High concurrency for speed
- `--grep-invert @enterprise` - Only run OSS tests
- `--quiet` - Minimal output

## Context

- Test files location: `frontend/e2e/tests/*.pw.ts`
- Test results: Individual test directories in `frontend/e2e/test-results/`
- **For EACH failed test**, a directory is created with these files:

## ALWAYS read these files in this order when debugging failures:

1. **`failed.json`** (in `test-results/` root) - START HERE
   - Contains only failed tests with error messages, stack traces, file paths, line numbers
   - Much smaller than results.json - only failures

2. **`error-context.md`** (in each failed test directory) - READ THIS SECOND
   - **THIS IS THE MOST VALUABLE FILE** - shows exact page state when test failed
   - YAML tree structure of the entire DOM with element states
   - Shows which buttons are disabled/enabled
   - Shows form field values
   - Shows what's visible on the page
   - Example: Can see if a button is `[disabled]` or a field is empty

3. **Trace files** (if needed for more detail):
   - Unzip `trace.zip` to get:
     - `0-trace.trace` - Every action taken with timestamps and selectors
     - `0-trace.network` - Network requests
     - Screenshots (jpegs) showing visual state at each step

4. **Full JSON report**: `results.json` - contains ALL test results (passed + failed), only use if needed

- **HTML report**: `frontend/e2e/playwright-report/` - browsable HTML interface (for humans, not programmatic use)
- Tests use Playwright with Firefox
- The retry logic is built into the test runner (via `run-with-retry.ts`)
- Tests run against a local Docker environment (API + DB)

## Workflow

**IMPORTANT: Always start by changing to the frontend directory** - the `.env` file and dependencies are located there.

1. **Run tests** from the frontend directory:
   ```bash
   cd frontend
   SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep-invert @enterprise --quiet
   ```

2. **ALWAYS check for flaky tests after test run completes:**

   **CRITICAL:** Tests that fail initially but pass on retry are FLAKY and MUST be investigated, even if the final result shows all tests passed.

   a. Check the test output for any tests that failed on first run (look for the initial failure messages before "Retrying")

   b. For EACH test that failed initially (even if it passed on retry):
      - Parse the error from the test output:
        * Error type (e.g., `TimeoutError`, `AssertionError`)
        * Error message (e.g., `"waiting for locator('#button') to be visible"`)
        * File path and line number where it failed
        * Stack trace showing the call chain
      - Read the test file at the failing line number to understand what was being tested
      - **Report these as FLAKY TESTS** - they indicate timing issues, race conditions, or environmental problems
      - **Analyze the root cause**:
        * Timeout errors → likely missing waits or race conditions
        * Assertion errors → check if value is correct or if timing is off
        * Element not found → selector may have changed or element loads slowly

   c. **If ANY tests are still failing after automatic retries:**

      For EACH failed test, **ALWAYS READ TRACES FIRST:**

      1. **Read error-context.md** in the failed test directory:
         - Shows exact DOM state when test failed
         - YAML tree with all elements, their states, and data-test attributes
         - Check if expected elements exist and their actual values
         - Verify selector is correct by searching for the data-test attribute

      2. **If error-context.md doesn't show the issue**, unzip and check trace files:
         ```bash
         cd frontend/e2e/test-results/<failed-test-directory>
         unzip -q trace.zip
         grep -i "error\|failed" 0-trace.network  # Check for network errors
         ```

      3. **Only after analyzing traces**, read the test file and fix:
        - Wrong selector → Update to match actual DOM from error-context.md
        - Missing `data-test` attribute → Add it to the component
        - Element hidden → Filter for visible elements or wait for visibility
        - Missing wait → Add appropriate `waitFor*` calls
        - Race condition → Add network waits, increase timeouts, or use more specific waits
        - Flaky element interaction → Add `scrollIntoView` or `waitForVisible` before clicking

   d. **After making fixes**, re-run ONLY the failed tests:
      ```bash
      cd frontend
      SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts tests/invite-test.pw.ts
      ```
      - Use concurrency=1 to avoid race conditions
      - Only run the specific test files that failed

   e. **If tests still fail after fixes:**
      - Try a second round of fixes if the error changed
      - Otherwise, report the issue with details on what was attempted

3. **Report final results:**
   - **ALWAYS report flaky tests first** (tests that failed initially but passed on retry)
   - List which tests passed/failed after all retries
   - Document any fixes that were applied
   - For unfixable issues, explain why and suggest manual investigation
   - Show the error message and line number for any failures

## Important Notes

- **DO NOT** just report that retries passed - if tests failed initially, investigate and fix the root cause
- **DO** modify test files to fix timing issues, missing waits, or broken selectors
- **DO** add `data-test` attributes to components if they're missing
- **DON'T** modify test assertions or business logic unless the test is clearly wrong
- If the failure is in application code (not test code), report it as a bug but don't try to fix it
- Always explain what fixes you're attempting and why
- Test files are in TypeScript and use the `helpers.playwright.ts` helper functions
- The built-in retry mechanism is a safety net, not a substitute for fixing flaky tests
