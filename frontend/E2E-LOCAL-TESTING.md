# Running E2E Tests Locally

## Quick Start

From the `frontend/` directory:

```bash
# Run all tests in Docker (like CI)
make test

# Run OSS tests only
make test-oss

# Run enterprise tests only
make test-enterprise

# Run with custom concurrency
E2E_CONCURRENCY=1 make test-oss
```

## Environment Variables

- `E2E_CONCURRENCY`: Number of parallel test workers (default: 3)
- `E2E_RETRIES`: Number of times to retry failed tests (default: 1)
- `SKIP_BUNDLE`: Skip bundle build step (`SKIP_BUNDLE=1`)
- `VERBOSE`: Show detailed output (`VERBOSE=1`, quiet by default)

## Running Tests

### Docker (matches CI exactly)
```bash
# OSS tests only
make test-oss

# Enterprise tests only
make test-enterprise

# All tests (OSS + Enterprise)
make test opts="--grep '@oss|@enterprise'"

# Specific test file
make test opts="tests/flag-tests.pw.ts"

# Skip bundle build for faster iteration
SKIP_BUNDLE=1 make test opts="tests/flag-tests.pw.ts"

# Verbose output
VERBOSE=1 make test-oss
```

### Keep Services Running
```bash
# Start services
docker compose -f docker-compose-e2e-tests.yml up -d

# Run tests (with retry logic)
docker compose -f docker-compose-e2e-tests.yml run --rm frontend \
    npm run test -- --grep @oss

# Re-run without rebuilding
SKIP_BUNDLE=1 docker compose -f docker-compose-e2e-tests.yml run --rm frontend \
    npm run test -- --grep @oss

# Check logs
docker compose -f docker-compose-e2e-tests.yml logs -f flagsmith-api

# Cleanup
docker compose -f docker-compose-e2e-tests.yml down
```

## Test Results

Results are saved to `e2e/test-results/` and `e2e/playwright-report/`:

```bash
# View HTML report
npx playwright show-report e2e/playwright-report

# Or open directly
open e2e/playwright-report/index.html
```

## Retry Behavior

Tests automatically retry on failure:
1. First attempt runs all tests
2. On failure, runs teardown to clean test data
3. Retries only failed tests (via `--last-failed`)
4. Controlled by `E2E_RETRIES` (default: 1 retry)

## Troubleshooting

### Rebuild images
```bash
docker compose -f docker-compose-e2e-tests.yml build --no-cache
```

### Port conflicts
```bash
docker compose -f docker-compose-e2e-tests.yml down
lsof -ti:8000  # Check what's using port 8000
```

### Using CI images
```bash
export API_IMAGE=ghcr.io/flagsmith/flagsmith-api:pr-1234
export E2E_IMAGE=ghcr.io/flagsmith/flagsmith-e2e:pr-1234
make test
```
