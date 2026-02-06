## Flagsmith Frontend

### Development

```bash
npm install
npm run dev
```

### E2E Testing

E2E tests use Playwright with Firefox and include videos, traces, and HTML reports for debugging.

#### Prerequisites

1. Docker running with Flagsmith services: `docker compose up -d`
2. Environment variables in `docker-compose.yml`:
   ```yaml
   E2E_TEST_AUTH_TOKEN: 'some-token'
   ENABLE_FE_E2E: 'true'
   ```
3. Matching token in `frontend/.env`:
   ```bash
   E2E_TEST_TOKEN_DEV=some-token
   ```

#### Running Tests

```bash
# Run all tests (builds bundle automatically)
npm run test

# Run with Playwright UI (for debugging - build bundle first)
npm run bundle
npm run test:dev

# Run specific test file
npm run test -- tests/flag-tests.pw.ts

# Run only OSS tests
npm run test -- --grep @oss

# Run only Enterprise tests
npm run test -- --grep @enterprise
```

#### Environment Variables

| Variable | Description |
|----------|-------------|
| `SKIP_BUNDLE=1` | Skip webpack build for faster iteration |
| `E2E_CONCURRENCY=N` | Number of parallel workers (default: 20, use 1 for debugging) |
| `E2E_RETRIES=0` | Fail-fast mode - stop on first failure |
| `E2E_REPEAT=N` | Run tests N additional times after passing to detect flakiness |

#### Examples

```bash
# Fast iteration (skip bundle, fail on first error)
E2E_RETRIES=0 SKIP_BUNDLE=1 npm run test -- tests/flag-tests.pw.ts

# Check for flaky tests (run 5 extra times after passing)
E2E_REPEAT=5 npm run test -- tests/flag-tests.pw.ts

# Debug with low concurrency
E2E_RETRIES=0 SKIP_BUNDLE=1 E2E_CONCURRENCY=1 npm run test -- tests/flag-tests.pw.ts
```

#### Test Results

- **HTML Report**: `e2e/playwright-report/` - Interactive dashboard with search/filter
- **Test Artifacts**: `e2e/test-results/` - Contains for each failed test:
  - `error-context.md` - DOM snapshot at failure point
  - `trace.zip` - Interactive trace viewer
  - Screenshots and videos

#### Claude Code Commands

When using Claude Code, these commands are available for e2e testing:

- `/e2e [N]` - Run all tests (OSS + Enterprise), auto-fix failures, re-run until passing
- `/e2e-oss [N]` - Run OSS tests only, auto-fix failures, re-run until passing
- `/e2e-ee [N]` - Run Enterprise tests only, auto-fix failures, re-run until passing
- `/e2e-create [description]` - Create a new test following existing patterns

The optional `[N]` argument sets `E2E_REPEAT` to run tests N additional times after passing (defaults to 0). E.g., `/e2e 5` runs tests, then repeats 5 more times to detect flakiness.
