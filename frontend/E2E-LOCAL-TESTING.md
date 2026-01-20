# Running E2E Tests Locally (Exactly Like CI)

This guide shows you how to run E2E tests in the exact same Docker environment used by GitHub Actions.

## Quick Start

From the `frontend/` directory:

```bash
./e2e/run-e2e-local.sh
```

This script will:
1. ✅ Build the API and E2E Docker images
2. ✅ Start PostgreSQL and Flagsmith API
3. ✅ Wait for API to be healthy
4. ✅ Run E2E tests with `--grep @oss` (same as CI)
5. ✅ Save test results and HTML reports locally
6. ✅ Clean up containers

## What Gets Built

The script builds two Docker images:

### 1. Flagsmith API (`flagsmith-api`)
- Built from the root `Dockerfile` with target `oss-api`
- Includes the Python API backend
- Uses PostgreSQL 15

### 2. E2E Frontend (`flagsmith-e2e`)
- Built from `frontend/Dockerfile.e2e`
- Contains the frontend code + Playwright + Firefox
- Configured for E2E testing environment

## Environment Matches CI Exactly

| CI Setting | Local Script |
|------------|--------------|
| API Image | Built locally with target `oss-api` |
| E2E Image | Built locally from `Dockerfile.e2e` |
| Test Args | `--grep @oss` |
| Concurrency | `E2E_CONCURRENCY=3` (configurable) |
| Browser | Firefox |

## Viewing Test Results

After tests run, results are saved to:

```bash
# View HTML report interactively
npx playwright show-report e2e/playwright-report

# Or just open the report
open e2e/playwright-report/index.html

# Raw test results (screenshots, traces, videos)
ls e2e/test-results/
```

## Customizing Test Runs

### Run Specific Tests
```bash
# Modify the script or run docker compose directly
docker compose -f docker-compose-e2e-tests.yml run --rm frontend \
    npm run test -- --grep "Environment Tests"
```

### Change Concurrency
```bash
E2E_CONCURRENCY=1 ./run-e2e-local.sh
```

### Keep Services Running for Debugging
```bash
# Start services manually
docker compose -f docker-compose-e2e-tests.yml up -d

# Run tests manually
docker compose -f docker-compose-e2e-tests.yml run --rm \
    -v "$(pwd)/e2e/test-results:/srv/flagsmith/e2e/test-results" \
    -v "$(pwd)/e2e/playwright-report:/srv/flagsmith/e2e/playwright-report" \
    frontend npm run test -- --grep @oss

# Services stay running - you can re-run tests, check API logs, etc.
docker compose -f docker-compose-e2e-tests.yml logs -f flagsmith-api

# Cleanup when done
docker compose -f docker-compose-e2e-tests.yml down
```

## Troubleshooting

### Tests Timeout Waiting for API
```bash
# Check API logs
docker compose -f docker-compose-e2e-tests.yml logs flagsmith-api

# Check API health
docker compose -f docker-compose-e2e-tests.yml ps
```

### Tests Fail Due to Missing Dependencies
```bash
# Rebuild images without cache
docker compose -f docker-compose-e2e-tests.yml build --no-cache
```

### Port Conflicts (8000 or 3000 in use)
```bash
# Check what's using the ports
lsof -ti:8000
lsof -ti:3000

# Kill existing containers
docker compose -f docker-compose-e2e-tests.yml down
```

### Test Results Not Appearing
The script mounts volumes to capture results. If you see permission errors:
```bash
# Ensure directories exist and are writable
mkdir -p e2e/test-results e2e/playwright-report
chmod 755 e2e/test-results e2e/playwright-report
```

## Comparing with CI

To verify your local environment matches CI:

1. **Check Docker Image Tags**: CI uses `ghcr.io/flagsmith/flagsmith-api:pr-XXX` and `ghcr.io/flagsmith/flagsmith-e2e:pr-XXX`, but locally we build fresh
2. **Check Test Output**: Compare test counts and failures with CI logs
3. **Check Browser Version**: Run `docker compose run frontend npx playwright --version`

## Advanced: Using CI-Built Images

To test with the exact images from CI (after they're built):

```bash
# Pull the images from a PR
export API_IMAGE=ghcr.io/flagsmith/flagsmith-api:pr-1234
export E2E_IMAGE=ghcr.io/flagsmith/flagsmith-e2e:pr-1234

# Run tests with pulled images (no build step)
docker compose -f docker-compose-e2e-tests.yml up -d db flagsmith-api
docker compose -f docker-compose-e2e-tests.yml run --rm frontend npm run test -- --grep @oss
```

## Stress Testing for Stability

To verify tests are bulletproof and catch race conditions/intermittent failures:

```bash
# Build Docker images first (optional - stress test will do this if needed)
npm run test:stress:build

# Run stress test (5 iterations with concurrency 16)
npm run test:stress

# Or directly
./e2e/run-e2e-stress-test.sh 5

# Custom iterations
./e2e/run-e2e-stress-test.sh 10

# Continue on failure (don't exit immediately)
FAIL_FAST=false ./e2e/run-e2e-stress-test.sh 5

# Force rebuild of Docker images
FORCE_BUILD=true npm run test:stress
```

**Stress test behavior:**
- Runs multiple iterations at high concurrency (16 workers, matching CI)
- **Exits immediately on first failure** (by default) to save time
- Saves failed test artifacts to `e2e/failed-runs/`
- Provides summary of pass/fail counts

**When to use:**
- Before pushing major E2E test changes
- When debugging intermittent test failures
- To verify login/auth flows are stable under load

## What's Different from `make test`?

The Makefile `make test` command is similar but:
- ✅ `e2e/run-e2e-local.sh`: Builds images, manages lifecycle, saves results
- ✅ `e2e/run-e2e-stress-test.sh`: Runs multiple iterations to catch intermittent issues
- ⚠️ `make test`: Assumes images exist, less output, harder to debug

Use `e2e/run-e2e-local.sh` for development and debugging.
Use `e2e/run-e2e-stress-test.sh` (or `npm run test:stress`) to verify stability.
Use `make test` if you just need a quick test run.
