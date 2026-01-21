# Optimise E2E Tests

Clean up E2E tests by removing unnecessary timeouts/waits and documenting necessary ones.

## Context

- Test files location: `frontend/e2e/tests/*.pw.ts`
- Test helpers: `frontend/e2e/helpers.playwright.ts`
- Test results: Individual test directories in `frontend/e2e/test-results/`
- **For EACH failed test**, a directory is created with these files:
  - `failed.json` - Summary of failures with error messages and stack traces
  - `error-context.md` - **MOST VALUABLE** - Page snapshot showing DOM state, field values, button states
  - `trace.zip` - Detailed execution trace (unzip to get action logs)
  - Screenshots (`.png`) and videos (`.webm`)
- Tests should be fast, reliable, and well-documented

## Workflow

**IMPORTANT: Always start by changing to the frontend directory** - the `.env` file and dependencies are located there.

1. **Scan all test files:**
   ```bash
   cd frontend
   ls e2e/tests/*.pw.ts
   ```

2. **For each test file, look for:**

   a. **Unnecessary timeouts/delays:**
   - `await page.waitForTimeout(5000)` - arbitrary waits
   - `setTimeout()` calls
   - Excessive `timeout` values in `waitFor*` calls
   - **Action:** Remove if not needed, or replace with specific waits like `waitForSelector`, `waitForLoadState`, `waitForResponse`

   b. **Hacky/unclear code:**
   - Multiple retry loops
   - Try-catch blocks hiding real issues
   - Commented-out code
   - Complex workarounds
   - **Action:** Refactor to be clearer or remove if obsolete

   c. **Missing explanations:**
   - Necessary waits without comments explaining why
   - Complex selectors without context
   - Non-obvious test logic
   - **Action:** Add clear comments explaining the "why"

3. **For necessary timeouts, add explanatory comments:**
   ```typescript
   // Wait for debounced search input (500ms debounce + network request)
   await page.waitForTimeout(1000);

   // Wait for animation to complete before asserting final state
   await page.waitForTimeout(300);

   // Wait for backend to process async task before checking result
   await page.waitForResponse(resp => resp.url().includes('/api/tasks/'));
   ```

4. **Replace arbitrary waits with specific ones:**
   ```typescript
   // BAD
   await page.waitForTimeout(3000);
   await page.click('#button');

   // GOOD
   await page.waitForSelector('#button', { state: 'visible' });
   await page.click('#button');

   // BETTER (if using helpers)
   await waitForElementVisible(page, '#button');
   await click(page, '#button');
   ```

5. **Test the optimised files:**
   - After making changes to a test file, run it multiple times to verify stability
   - Run each modified test file 3 times with concurrency=1:
     ```bash
     cd frontend
     for i in {1..3}; do
       echo "Run $i/3"
       SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/modified-test.pw.ts --quiet
     done
     ```
   - **If any run fails, ALWAYS READ TRACES FIRST:**
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
     3. **Only after analyzing traces**, investigate whether the optimisation caused it:
        - Wrong selector → Update to match actual DOM from error-context.md
        - Missing wait → If optimisation removed a necessary wait, add it back with proper comment explaining why it's needed
        - Element hidden → Check if removed wait was allowing element to become visible
        - Race condition → If timeout removal caused timing issue, use event-based wait instead
   - Only keep optimisations that pass all 3 runs consistently

6. **Report changes:**
   - List files modified and verified
   - Show timeouts removed vs. timeouts kept with explanations
   - Note any complex code that was simplified
   - Report test stability (3/3 passes for each modified file)
   - Suggest further improvements if needed

## Important Notes

- **DO** remove arbitrary `waitForTimeout()` calls that can be replaced with event-based waits
- **DO** add comments for necessary waits explaining the exact reason
- **DO** simplify complex workarounds where possible
- **DON'T** remove waits that are necessary for animations, debouncing, or async backend operations
- **DON'T** change test logic or assertions
- Focus on making tests faster and more maintainable
- Every timeout should have a comment or be replaced with a better wait
