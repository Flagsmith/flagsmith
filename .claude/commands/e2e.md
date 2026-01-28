# E2E Test Runner with Auto-Fix (All Tests)

**IMMEDIATELY run all E2E tests (both OSS and enterprise), analyze failures, fix them, and re-run failed tests until all pass or unfixable issues are identified.**

## Arguments

If an argument is provided (e.g., `/e2e 5`), run tests that many times to detect flakiness.

- `$ARGUMENTS` = "" → Run tests once (default)
- `$ARGUMENTS` = "5" → Run tests 5 times, stopping on first failure

## Prerequisites
Read `.claude/context/e2e.md` for full E2E configuration details and setup requirements.

## CRITICAL: Stop on Failure

**On ANY test failure, you MUST:**
1. Read error-context.md for the failed test
2. **STOP and report the failure summary to the user**
3. **Ask for user consent before doing ANYTHING else** (no investigating, no fixing, no additional iterations)

Only proceed with investigation/fixes after the user explicitly approves.

## Multiple Iterations

**NEVER use `E2E_REPEAT` environment variable.** It runs automatically and clears reports, destroying error context.

When running multiple iterations:
1. Run tests **one iteration at a time** using separate bash commands
2. **STOP IMMEDIATELY** on any failure - do not continue to next iteration
3. Track iteration count: "Iteration X of Y passed"
4. Ask user before continuing to next iteration

## Workflow

**IMPORTANT: Always start by changing to the frontend directory** - the `.env` file and dependencies are located there.

1. **RUN TESTS NOW** from the frontend directory (ONE iteration):
   ```bash
   cd frontend
   E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --quiet
   ```

   **Note:** Using `E2E_RETRIES=0` to fail fast on first failure for immediate analysis and fixing.

   If multiple iterations requested and tests pass, report "Iteration 1 of N passed" and ask before continuing.

2. **If ANY tests fail:**

   a. **Read error-context.md** in the failed test directory:
      - Check `frontend/e2e/test-results/<test-directory>/error-context.md`

   b. **STOP and report to user:**
      - Summarize what failed and the error from error-context.md
      - Ask: "Would you like me to investigate and fix this?"
      - **DO NOT proceed until user confirms**

   c. **Only after user approval**, investigate further if needed:
      - If error-context.md doesn't show the issue, unzip and check trace files:
      ```bash
      cd frontend/e2e/test-results/<failed-test-directory>
      unzip -q trace.zip
      grep -i "error\|failed" 0-trace.network  # Check for network errors
      ```

   d. **Only after analysing traces**, read the test file and fix:
      - Wrong selector → Update to match actual DOM from error-context.md
      - Missing `data-test` attribute → Add it to the component
      - Element hidden → Filter for visible elements or wait for visibility
      - Missing wait → Add appropriate `waitFor*` calls
      - Race condition → Add network waits, increase timeouts, or use more specific waits
      - Flaky element interaction → Add `scrollIntoView` or `waitForVisible` before clicking

   e. **After making fixes**, re-run ONLY the failed tests:
      ```bash
      cd frontend
      E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts tests/invite-test.pw.ts
      ```
      - Use `E2E_RETRIES=0` to fail fast and see if the fix worked
      - Use concurrency=1 to avoid race conditions
      - Only run the specific test files that failed

   f. **Repeat the fix/re-run cycle:**
      - If tests still fail after fixes but the error changed, analyse the new error and fix again
      - Re-run failed tests after each fix attempt
      - Continue until all tests pass or you've identified unfixable issues
      - Maximum 3 fix/re-run cycles per test before reporting as unfixable

3. **Report final results:**
   - Break down results by category:
     - OSS tests: X passed / Y failed
     - Enterprise tests: X passed / Y failed
     - Total: X passed / Y failed
   - List which tests passed/failed
   - Document any fixes that were applied
   - For unfixable issues, explain why and suggest manual investigation
   - Show the error message and line number for any failures

## Important Notes

- **DO** modify test files to fix timing issues, missing waits, or broken selectors
- **DO** add `data-test` attributes to components if they're missing
- **DON'T** modify test assertions or business logic unless the test is clearly wrong
- If the failure is in application code (not test code), report it as a bug but don't try to fix it
- Always explain what fixes you're attempting and why
- Test files are in TypeScript and use the `helpers.playwright.ts` helper functions
- With `E2E_RETRIES=0`, tests fail immediately without retries, preserving all error-context.md files in `test-results/`
