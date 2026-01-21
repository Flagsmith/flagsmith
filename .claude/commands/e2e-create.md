# E2E Test Creator

Create a new E2E test following the existing patterns in the codebase.

## Context

- Test files location: `frontend/e2e/tests/*.pw.ts`
- Test helpers: `frontend/e2e/helpers.playwright.ts`
- Existing tests to reference for patterns
- Tests use Playwright with Firefox
- Tests are tagged with `@oss` or `@enterprise`

## Workflow

1. **Ask the user what they want to test:**
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

6. **Report what was created:**
   - Show the test file path
   - List any `data-test` attributes that were added
   - Suggest how to run the test

## Important Notes

- Always use `data-test` attributes for selectors, not CSS classes or IDs
- Use existing helper functions instead of raw Playwright APIs
- Follow the login pattern from other tests
- Tests should be independent and not rely on order of execution
- Use descriptive test names that explain what's being tested
- Add appropriate waits for async operations
