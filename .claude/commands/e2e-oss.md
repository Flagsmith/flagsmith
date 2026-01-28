# E2E OSS Test Runner with Auto-Fix

**IMMEDIATELY run OSS (non-enterprise) E2E tests, analyse failures, fix them, and re-run failed tests until all pass or unfixable issues are identified.**

## Prerequisites
Read `.claude/context/e2e.md` for full E2E configuration details and setup requirements.

## Workflow

**IMPORTANT: Always start by changing to the frontend directory** - the `.env` file and dependencies are located there.

1. **RUN TESTS NOW** from the frontend directory:
   ```bash
   cd frontend
   E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep-invert @enterprise --quiet
   ```

   **Note:** Using `E2E_RETRIES=0` to fail fast on first failure for immediate analysis and fixing.

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
      E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts tests/invite-test.pw.ts
      ```
      - Use `E2E_RETRIES=0` to fail fast and see if the fix worked
      - Use concurrency=1 to avoid race conditions
      - Only run the specific test files that failed

   e. **Repeat the fix/re-run cycle:**
      - If tests still fail after fixes but the error changed, analyze the new error and fix again
      - Re-run failed tests after each fix attempt
      - Continue until all tests pass or you've identified unfixable issues
      - Maximum 3 fix/re-run cycles per test before reporting as unfixable

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
