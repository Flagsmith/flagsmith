# E2E Testing Configuration and Context

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
  - OSS tests: Default tests (use `--grep-invert @enterprise`)
  - Enterprise tests: Tagged with `@enterprise` (use `--grep @enterprise`)

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
- Browsable interface for viewing test results

## Running E2E Tests

### Prerequisites
1. Ensure Docker is running
2. Start Flagsmith services: `docker compose up -d`
3. Verify E2E is configured:
   ```bash
   docker exec flagsmith-flagsmith-1 python -c "import os; print('E2E_TEST_AUTH_TOKEN:', os.getenv('E2E_TEST_AUTH_TOKEN')); print('ENABLE_FE_E2E:', os.getenv('ENABLE_FE_E2E'))"
   ```

### Test Commands

#### Run OSS Tests
```bash
cd frontend
SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep-invert @enterprise --quiet
```

#### Run Enterprise Tests
```bash
cd frontend
SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep @enterprise --quiet
```

#### Run Specific Test Files
```bash
cd frontend
SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts tests/invite-test.pw.ts
```

#### Run All Tests (OSS + Enterprise)
```bash
cd frontend
SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --quiet
```

#### Fail-Fast Mode (Stop on First Failure)
When debugging, use `E2E_RETRIES=0` to stop immediately after the first test failure without running remaining tests or retrying:
```bash
cd frontend
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep @enterprise --quiet
```

**Note**: Playwright will finish running tests that are already in progress (due to parallel execution), but won't start any new tests after the first failure. For truly immediate failure (one test at a time), combine with `E2E_CONCURRENCY=1`:
```bash
cd frontend
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- --grep @enterprise --quiet
```

### Environment Variables
- `SKIP_BUNDLE=1` - Skip webpack bundle build for faster iteration
- `E2E_CONCURRENCY=20` - Number of parallel test workers (reduce to 1 for debugging)
- `E2E_RETRIES=0` - Disable retries and enable fail-fast mode (stop on first failure)
- `E2E_REPEAT=N` - After tests pass, run them N additional times to detect flakiness
- `--quiet` - Minimal output
- `--grep @enterprise` - Run only enterprise tests
- `--grep-invert @enterprise` - Run only OSS tests
- `-x` - Stop after first failure (automatically added when `E2E_RETRIES=0`)

#### Flakiness Detection Mode
To check for flaky tests, use `E2E_REPEAT` to run tests multiple times:
```bash
cd frontend
SKIP_BUNDLE=1 E2E_CONCURRENCY=20 E2E_REPEAT=5 npm run test -- --quiet
```
This runs tests once, then if they pass, repeats 5 more times. If any repeat fails, the test is flagged as flaky.

## Backend E2E Implementation

### Teardown Endpoint
- URL: `/api/v1/e2etests/teardown/`
- Method: POST
- Authentication: Via `X-E2E-Test-Auth-Token` header
- Purpose: Clears test data and re-seeds database between test runs

### Middleware
The backend uses `E2ETestMiddleware` to:
1. Check for `X-E2E-Test-Auth-Token` header
2. Compare against `E2E_TEST_AUTH_TOKEN` environment variable
3. Set `request.is_e2e = True` if authenticated

### Settings Required
- `E2E_TEST_AUTH_TOKEN`: Token for authentication
- `ENABLE_FE_E2E`: Must be `True` to enable endpoints

## Debugging Test Failures

### Reading Order for Failed Tests
1. **`failed.json`** - Start here for error summary
2. **`error-context.md`** - DOM snapshot showing exact page state
3. **`trace.zip`** - Detailed trace if needed

### Common Issues and Solutions

#### Authentication Errors (401)
- Verify `E2E_TEST_AUTH_TOKEN` is set in docker-compose.yml
- Check token matches in frontend `.env` file
- Restart containers after configuration changes

#### Bad Request Errors (400)
- Ensure `ENABLE_FE_E2E: 'true'` is set in docker-compose.yml
- Restart containers to apply settings

#### Flaky Tests
- Tests that fail initially but pass on retry indicate:
  - Missing waits or race conditions
  - Timing issues with element visibility
  - Network request timing issues
- Always investigate and fix root causes

### Test Helpers
- Helper functions: `frontend/e2e/helpers.playwright.ts`
- Use data-test attributes for reliable selectors
- Prefer explicit waits over arbitrary delays

## Test Infrastructure

### Playwright Configuration
- Browser: Firefox
- Test runner: `frontend/e2e/run-with-retry.ts`
- Global setup: `frontend/e2e/global-setup.playwright.ts`
- Global teardown: `frontend/e2e/global-teardown.playwright.ts`

### Retry Logic
- Built-in retry mechanism in `run-with-retry.ts`
- Retries are a safety net, not a solution for flaky tests
- All flaky tests must be investigated and fixed

## Best Practices

1. **Always run from frontend directory** - Dependencies and .env file are there
2. **Check for flaky tests** - Even if they pass on retry
3. **Read error-context.md first** - Shows exact DOM state at failure
4. **Use low concurrency for debugging** - Set E2E_CONCURRENCY=1
5. **Don't ignore timing issues** - Fix root causes of flakiness
6. **Add data-test attributes** - For reliable element selection
7. **Document fixes** - Explain what was changed and why

## Claude-Specific Instructions

**CRITICAL: Never use E2E_REPEAT environment variable.** It runs tests automatically without control and clears reports on each iteration, destroying error context needed for debugging.

When asked to run tests multiple times (e.g., `/e2e 5`):
1. Run tests **one iteration at a time** using separate bash commands
2. **Stop immediately** on any failure - do not continue to the next iteration
3. **Report the failure** and analyze error-context.md before proceeding
4. **Ask for user consent** before running additional iterations
5. Preserve test artifacts by never running commands that clear reports after a failure

Example for 5 iterations:
```bash
# Run iteration 1
FLAGSMITH_API_URL="http://localhost:8000/api/v1/" E2E_TEST_TOKEN=some-token E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=20 npm run test -- --grep-invert @enterprise --quiet
# If passed, report and ask user before running iteration 2
# If failed, STOP and analyze - do not continue
```