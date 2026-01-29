# E2E Test Creator

Create a new E2E test following the existing patterns in the codebase.

## Arguments

- `$ARGUMENTS` = "" → Ask the user what to test
- `$ARGUMENTS` = "segment creation flow" → Create a test for that feature

## CRITICAL: Read Context First

**You MUST read `.claude/context/e2e.md` before proceeding.** It contains essential configuration, test structure, and debugging guides.

## Workflow

1. **Determine what to test:**
   - If `$ARGUMENTS` is provided, use that as the test description
   - Otherwise, ask the user what feature/page/flow to test

2. **Determine if OSS or Enterprise:**
   - Check if the feature exists in enterprise-only code paths
   - Tag the test with `@oss` or `@enterprise` accordingly

3. **Review existing patterns:**
   - Read 2-3 similar test files from `frontend/e2e/tests/`
   - Read `frontend/e2e/helpers.playwright.ts` for available utilities

4. **Scan application code:**
   - Find components being tested in `frontend/web/components/` or `frontend/common/`
   - Add `data-test` attributes if missing

5. **Create the test file:**
   - Follow naming convention: `*-test.pw.ts` or `*-tests.pw.ts`
   - Use helper functions from `helpers.playwright.ts`

6. **Verify the test works:**
   ```bash
   cd frontend
   SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/new-test.pw.ts --quiet
   ```
   Run twice to check for flakiness. On failure, follow the analysis workflow in context/e2e.md.

7. **Report what was created:**
   - Test file path
   - Any `data-test` attributes added
   - Test stability results

## Important Notes

- Always use `data-test` attributes for selectors
- Use existing helper functions instead of raw Playwright APIs
- Tests should be independent and not rely on execution order
