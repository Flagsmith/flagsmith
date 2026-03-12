## Flagsmith Frontend

### Docker-based development

To bring up the API and database via Docker Compose:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

The application will bootstrap an admin user, organisation, and project for you. You'll find a link to set your password in your Compose logs:

```txt
Superuser "admin@example.com" created successfully.
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/.../...
```

### Local development

The project assumes the following tools installed:
- [Node.js](https://nodejs.org/) version 22.x
- [npm](https://www.npmjs.com/) version 10.x

To install dependencies, run `npm install`.

The API must be running on localhost:8000 (either via Docker or `make serve` in `../api`).

To bring up a dev server, run `ENV=local npm run dev`.

To run linters, run `npm run lint` (or `npm run lint:fix` to auto-fix).

To run type checking, run `npm run typecheck`.

### Environment configuration

Environment configuration is defined in `project_*.js` files (`common/project.js` for defaults, `env/project_*.js` for staging/prod/selfhosted), selected at build time based on the target environment. All configs support runtime overrides via `globalThis.projectOverrides`, allowing deployment-time customisation without rebuilding.

The `bin/env.js` script copies the appropriate `env/project_${ENV}.js` to `common/project.js`:
- `npm run dev` → copies `project_dev.js` (staging API)
- `ENV=local npm run dev` → copies `project_local.js` (localhost)
- `ENV=prod npm run bundle` → copies `project_prod.js` (production)

For a full list of frontend environment variables, see the [Flagsmith documentation](https://docs.flagsmith.com/deployment/hosting/locally-frontend#environment-variables).

### Code guidelines

#### Testing

**Unit tests** use Jest and are located in `__tests__/` directories next to source files.

To run unit tests, run `npm run test:unit`.

To run a specific test file: `npm run test:unit -- --testPathPatterns={filename}`

**E2E tests** use TestCafe and are located in the `e2e/` directory.

To run E2E tests (requires the API running on localhost:8000), run `npm run test`.

#### Typing

This codebase uses TypeScript. Run `npm run typecheck` to check for type errors.

We encourage adding types to new code and improving types in existing code when working nearby.

#### Design and architecture

The frontend is organised into:
- `common/` - Shared code (Redux store, RTK Query services, types, utilities)
- `web/components/` - React components
- `web/components/pages/` - Page-level components

State management uses Redux Toolkit with RTK Query for API calls. Services are defined in `common/services/`.

API types are centralised in:
- `common/types/requests.ts` - Request types
- `common/types/responses.ts` - Response types

For AI-assisted development, see [CLAUDE.md](https://github.com/Flagsmith/flagsmith/blob/main/frontend/CLAUDE.md).

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
