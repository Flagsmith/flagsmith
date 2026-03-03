# E2E Testing Configuration and Context

**CRITICAL: This file MUST be read before running any E2E commands. It contains essential configuration, debugging guides, and workflow instructions that all E2E commands depend on.**

## Docker Configuration

To run E2E tests, the following environment variables must be set in `docker-compose.yml` for the `flagsmith` service:

```yaml
# E2E Testing
E2E_TEST_AUTH_TOKEN: 'some-token'  # Authentication token for E2E teardown endpoint
ENABLE_FE_E2E: 'true'               # Enables the E2E testing endpoints in the backend
```

## Frontend Configuration

The frontend `.env` file should contain tokens for different environments:

```bash
E2E_TEST_TOKEN_DEV=some-token
E2E_TEST_TOKEN_LOCAL=some-token
E2E_TEST_TOKEN_STAGING=<staging-token>
E2E_TEST_TOKEN_PROD=<prod-token>
```

## Test Organization

### Test Files
- Location: `frontend/e2e/tests/*.pw.ts`
- Test categories:
  - OSS tests: Tagged with `@oss` (use `--grep @oss`)
  - Enterprise tests: Tagged with `@enterprise` (use `--grep @enterprise`)
  - All tests: `--grep "@oss|@enterprise"`

### Test Results
- Results directory: `frontend/e2e/test-results/`
- Failed test artifacts:
  - `failed.json` - Summary of only failed tests
  - `results.json` - Complete test results (all tests)
  - Individual test directories containing:
    - `error-context.md` - DOM snapshot at failure point
    - `trace.zip` - Detailed execution trace
    - Screenshots of failures

### HTML Report
- Location: `frontend/e2e/playwright-report/`
- View with: `npm run test:report`

## Environment Variables

- `SKIP_BUNDLE=1` - Skip webpack bundle build for faster iteration
- `E2E_CONCURRENCY=20` - Number of parallel test workers (reduce to 1 for debugging)
- `E2E_RETRIES=0` - Disable retries and enable fail-fast mode (stop on first failure)
- `--quiet` - Minimal output
- `--grep @enterprise` - Run only enterprise tests
- `--grep @oss` - Run only OSS tests
- `--grep "@oss|@enterprise"` - Run all tests
- `-x` - Stop after first failure (automatically added when `E2E_RETRIES=0`)

## CRITICAL: Multiple Iterations

**NEVER use `E2E_REPEAT` environment variable.** It runs tests automatically without control and clears reports on each iteration, destroying error context needed for debugging.

When running multiple iterations:
1. Run tests **one iteration at a time** using separate bash commands
2. **STOP IMMEDIATELY** on any failure - do not continue to next iteration
3. Analyze error-context.md and report the failure
4. **Ask user for consent** before running additional iterations
5. Track iteration count: "Iteration X of Y passed"

## CRITICAL: Failure Analysis Workflow

**On ANY test failure, you MUST:**
1. Read error-context.md for the failed test
2. **STOP and report the failure summary to the user**
3. **Ask for user consent before doing ANYTHING else** (no investigating, no fixing, no additional iterations)

Only proceed with investigation/fixes after the user explicitly approves.

### Reading Order for Failed Tests

1. **`error-context.md`** - Start here for DOM snapshot showing exact page state
2. **`failed.json`** - Error summary
3. **`trace.zip`** - Detailed trace if needed

### Analyzing Traces

```bash
cd frontend/e2e/test-results/<failed-test-directory>
unzip -q trace.zip
grep -i "error\|failed" 0-trace.network  # Check for network errors
```

### Common Fix Patterns

- **Wrong selector** → Update to match actual DOM from error-context.md
- **Missing `data-test` attribute** → Add it to the component
- **Element hidden** → Filter for visible elements or wait for visibility
- **Missing wait** → Add appropriate `waitFor*` calls
- **Race condition** → Add network waits, increase timeouts, or use more specific waits
- **Flaky element interaction** → Add `scrollIntoView` or `waitForVisible` before clicking

### Re-running Failed Tests

After making fixes, re-run ONLY the failed tests:
```bash
cd frontend
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/specific-test.pw.ts
```

Maximum 3 fix/re-run cycles per test before reporting as unfixable.

## CRITICAL: Flaky Test Policy

Tests that fail initially but pass on retry are FLAKY and MUST be investigated, even if the final result shows all tests passed.

- **DO NOT** just report that retries passed
- **DO** investigate and fix the root cause
- The built-in retry mechanism is a safety net, not a substitute for fixing flaky tests

## Important Rules

- **DO** modify test files to fix timing issues, missing waits, or broken selectors
- **DO** add `data-test` attributes to components if they're missing
- **DON'T** modify test assertions or business logic unless the test is clearly wrong
- If the failure is in application code (not test code), report it as a bug but don't try to fix it
- Always explain what fixes you're attempting and why

## CRITICAL: Use Helpers, Not Raw Page Methods

**NEVER use `page.waitForTimeout()` or raw `page.locator()` methods.** Always use the helper functions instead:

### Wait Helpers (Use These Instead of waitForTimeout)
- `waitForElementVisible(selector)` - Wait for element to be visible
- `waitForElementClickable(selector)` - Wait for element to be clickable
- `waitForToast()` - Wait for toast notification
- `waitAndRefresh()` - Wait and refresh page state
- `waitForFeatureSwitch(name, state)` - Wait for feature switch state
- `waitForUserFeatureSwitch(name, state)` - Wait for user feature switch state

### Click Helpers (Use These Instead of page.locator().click())
- `click(selector)` - Click element (handles wait, scroll, enabled check)
- `clickByText(text, element)` - Click element by text content
- `clickUserFeature(name)` - Click user feature
- `clickUserFeatureSwitch(name, state)` - Click user feature switch

### Other Helpers
- `setText(selector, value)` - Set input text
- `closeModal()` - Close modal (instead of Escape key)
- `assertInputValue(selector, value)` - Assert input value
- `gotoFeatures()`, `gotoFeature(name)`, etc. - Navigation helpers

**Why?** Helpers include proper waiting, error handling, and scrolling. Raw page methods lead to flaky tests.

## Test Infrastructure

### Playwright Configuration
- Browser: Firefox
- Test runner: `frontend/e2e/run-with-retry.ts`
- Helper functions: `frontend/e2e/helpers.playwright.ts`
- Global setup: `frontend/e2e/global-setup.playwright.ts`
- Global teardown: `frontend/e2e/global-teardown.playwright.ts`

### Backend E2E Implementation

#### Teardown Endpoint
- URL: `/api/v1/e2etests/teardown/`
- Method: POST
- Authentication: Via `X-E2E-Test-Auth-Token` header
- Purpose: Clears test data and re-seeds database between test runs

#### Middleware
The backend uses `E2ETestMiddleware` to:
1. Check for `X-E2E-Test-Auth-Token` header
2. Compare against `E2E_TEST_AUTH_TOKEN` environment variable
3. Set `request.is_e2e = True` if authenticated

## Common Issues and Solutions

### Authentication Errors (401)
- Verify `E2E_TEST_AUTH_TOKEN` is set in docker-compose.yml
- Check token matches in frontend `.env` file
- Restart containers after configuration changes

### Bad Request Errors (400)
- Ensure `ENABLE_FE_E2E: 'true'` is set in docker-compose.yml
- Restart containers to apply settings
