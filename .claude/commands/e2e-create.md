# E2E Test Creator

Create a new E2E test following the existing patterns in the codebase.

## Arguments

If an argument is provided (e.g., `/e2e-create segment creation flow`), use it as the test description instead of asking.

- `$ARGUMENTS` = "" → Ask the user what to test
- `$ARGUMENTS` = "segment creation flow" → Create a test for segment creation

## Prerequisites
Read `.claude/context/e2e.md` for full E2E configuration details, test structure, and debugging guides.

## Workflow

**IMPORTANT: Always start by changing to the frontend directory** - the `.env` file and dependencies are located there.

1. **Determine what to test:**
   - If `$ARGUMENTS` is provided, use that as the test description
   - Otherwise, ask the user:
     - What feature/page/flow to test
     - Any specific scenarios or edge cases

2. **Determine if this is OSS or Enterprise:**
   - Check if the feature being tested exists in enterprise-only code paths
   - Look for clues in existing tests that test similar features
   - If unclear, ask the user
   - Tag the test with `@oss` or `@enterprise` accordingly

3. **Review existing test patterns:**
   - Read 2-3 similar existing test files from `frontend/e2e/tests/`
   - Read `frontend/e2e/helpers.playwright.ts` to understand available utilities
   - Note common patterns like:
     - Login flow
     - Navigation
     - Element selection using `data-test` attributes
     - Waiting for elements/network
     - Assertions

4. **Scan the relevant application code:**
   - Find the components/pages being tested in `frontend/web/components/` or `frontend/common/`
   - Check if elements already have `data-test` attributes
   - If missing, add `data-test` attributes to make tests reliable:
     - Use descriptive names like `data-test="create-feature-btn"`
     - Follow existing naming patterns in the codebase
     - Add them to buttons, inputs, and key interactive elements

5. **Create the test file:**
   - Follow the naming convention: `*-test.pw.ts` or `*-tests.pw.ts`
   - Use the test structure from existing tests
   - Use helper functions from `helpers.playwright.ts`
   - Include proper test descriptions and tags
   - Add comments explaining complex test logic

6. **Run the new test to verify it works:**
   - Run the test multiple times to check for flakiness (run each iteration separately, stopping on failure):
     ```bash
     cd frontend
     SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/new-test.pw.ts --quiet
     # If passed, run again to verify stability
     SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/new-test.pw.ts --quiet
     ```
   - **NEVER use E2E_REPEAT** - it clears reports and destroys error context
   - **If the test fails, ALWAYS READ TRACES FIRST:**
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
     3. **Only after analyzing traces**, fix the issue:
        - Wrong selector → Update to match actual DOM from error-context.md
        - Missing `data-test` attribute → Add it to the component
        - Element hidden → Filter for visible elements or wait for visibility
        - Missing wait → Add appropriate `waitFor*` calls
     - Re-run until it passes consistently

7. **Report what was created:**
   - Show the test file path
   - List any `data-test` attributes that were added
   - Report test stability (how many runs passed/failed)
   - If there were failures, explain what was fixed

## Important Notes

- Always use `data-test` attributes for selectors, not CSS classes or IDs
- Use existing helper functions instead of raw Playwright APIs
- Follow the login pattern from other tests
- Tests should be independent and not rely on order of execution
- Use descriptive test names that explain what's being tested
- Add appropriate waits for async operations
