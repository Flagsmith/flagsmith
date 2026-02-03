# E2E Test Fixes - Complete Solution

## Executive Summary

**Status:** ✅ All fixes applied and tested
**Test Results:** 10/10 tests passing (100%)
**Test Duration:** ~2.6 minutes

All E2E test issues in PR #6562 (Playwright migration) have been resolved. Tests now run reliably locally with zero database deadlocks and all segment/versioning tests passing.

## Problem Overview

The E2E tests were failing locally with two critical issues:

1. **Database Deadlock** - Concurrent teardown operations causing PostgreSQL deadlocks
2. **Edge API Misconfiguration** - Tests calling production API instead of local Docker API

These caused 6 out of 10 tests to fail consistently.

## Solution Applied

### 5 Files Modified

All changes are on the `chore/playwright` branch and ready to be incorporated into PR #6562.

---

## 1. Database Deadlock Fix (Backend)

**File:** `api/e2etests/e2e_seed_data.py`

**Problem:** Two separate mechanisms (retry logic + Playwright global setup) were calling teardown concurrently, causing database deadlocks.

**Solution:** Added PostgreSQL advisory locks to serialize teardown/seed operations.

**Changes:**
```python
# Added imports (line 13)
from django.db import connection, transaction

# Added lock constant (lines 35-37)
# Advisory lock ID for E2E teardown/seed serialization
# This prevents concurrent teardown operations that cause database deadlocks
E2E_TEARDOWN_LOCK_ID = 123456789

# Wrapped teardown() with advisory locks (lines 48-80)
def teardown() -> None:
    """
    Teardown and cleanup all E2E test data.
    Uses PostgreSQL advisory locks to prevent concurrent execution and deadlocks.
    """
    with connection.cursor() as cursor:
        # Acquire advisory lock - blocks if another teardown is in progress
        cursor.execute("SELECT pg_advisory_lock(%s)", [E2E_TEARDOWN_LOCK_ID])

        try:
            # Perform all teardown operations atomically
            with transaction.atomic():
                delete_user_and_its_organisations(user_email=settings.E2E_SIGNUP_USER)
                delete_user_and_its_organisations(user_email=settings.E2E_USER)
                # ... all other delete operations ...
        finally:
            # Always release the lock, even if an error occurred
            cursor.execute("SELECT pg_advisory_unlock(%s)", [E2E_TEARDOWN_LOCK_ID])

# Wrapped seed_data() with same lock (lines 83-238)
def seed_data() -> None:
    """
    Seed fresh E2E test data.
    Uses the same advisory lock as teardown() to ensure sequential execution.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", [E2E_TEARDOWN_LOCK_ID])

        try:
            with transaction.atomic():
                # All seed operations...
                pass
        finally:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [E2E_TEARDOWN_LOCK_ID])
```

**Why it works:**
- PostgreSQL advisory locks ensure only ONE teardown executes at a time
- Second concurrent call blocks (waits) instead of conflicting
- Atomic transactions ensure all-or-nothing database operations
- Locks always released in `finally` block, even on errors

---

## 2. Edge API Configuration Fix (Frontend)

**File:** `frontend/env/project_e2e.js`

**Problem:** E2E tests were configured to call external production Edge API (`https://edge.api.flagsmith.com/api/v1/`), which is unreachable from Docker and caused network errors.

**Solution:** Changed to local Docker API endpoint.

**Changes:**
```diff
- flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',
+ flagsmithClientAPI: 'http://flagsmith-api:8000/api/v1/',

- flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
+ flagsmithClientEdgeAPI: 'http://flagsmith-api:8000/api/v1/',
```

**Impact:** Fixed 6 failing tests (Segment 1-3, Versioning, Flag tests)

---

## 3. Remove Redundant Teardown (Frontend)

**File:** `frontend/e2e/run-with-retry.ts`

**Problem:** Manual teardown call after test failure raced with Playwright's automatic global setup teardown.

**Solution:** Removed redundant manual teardown.

**Changes:**
```diff
  if (attempt > 0) {
    if (!quietMode) {
      console.log('\n==========================================');
-     console.log(`Test attempt ${attempt} failed, running teardown and retrying failed tests only...`);
+     console.log(`Test attempt ${attempt} failed, retrying failed tests only...`);
      console.log('==========================================\n');
    }
-   await runTeardown();
+   // Note: Removed manual teardown call to prevent database deadlock
+   // Teardown is handled by globalSetup.playwright.ts before each test run
+   // await runTeardown();
  }
```

**Why it works:** Playwright's `globalSetup.playwright.ts` already handles teardown correctly before each test run.

---

## 4. Docker Compose Compatibility (Infrastructure)

**File:** `frontend/Makefile`

**Problem:** Hardcoded `docker compose` command failed on systems using standalone `docker-compose` binary.

**Solution:** Auto-detect which command is available.

**Changes:**
```diff
+ # Auto-detect Docker Compose command (V2 plugin or standalone)
+ DOCKER_COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

  test:
    @echo "Running E2E tests..."
-   @docker compose run --name e2e-test-run frontend \
+   @$(DOCKER_COMPOSE) run --name e2e-test-run frontend \
```

---

## 5. E2E Token Configuration (Infrastructure)

**File:** `frontend/docker-compose-e2e-tests.yml`

**Problem:** Missing `E2E_TEST_TOKEN` caused 401 errors from teardown endpoint.

**Solution:** Added token to frontend service environment.

**Changes:**
```diff
  frontend:
    environment:
+     E2E_TEST_TOKEN: some-token
      E2E_TEST_TOKEN_DEV: some-token
```

---

## Test Results

### Before Fixes
- **4/10 tests passing** (40%)
- Database deadlock errors
- Network errors to edge.api.flagsmith.com
- Organisation test failing (400 login error)
- Segment tests 1-3 failing (network timeout)
- Versioning tests failing (network timeout)

### After Fixes
- **10/10 tests passing** (100%) ✅
- Zero database deadlock errors ✅
- No network errors ✅
- Test duration: ~2.6 minutes ✅

### Test Breakdown
```
✓ 1 [firefox] › Signup › Create Organisation and Project @oss (12.2s)
✓ 2 [firefox] › Flag Tests › test description @oss (1.1m)
✓ 3 [firefox] › Environment Tests › test description @oss (10.4s)
✓ 4 [firefox] › Invite Tests › test description @oss (11.4s)
✓ 5 [firefox] › Organisation Tests › test description @oss (11.6s)
✓ 6 [firefox] › Project Tests › test description @oss (11.2s)
✓ 7 [firefox] › Segment test 1 - multivariate flags @oss (55.0s)
✓ 8 [firefox] › Segment test 2 - priority and overrides @oss (1.2m)
✓ 9 [firefox] › Segment test 3 - user-specific overrides @oss (38.7s)
✓ 10 [firefox] › Versioning tests - versions @oss (1.2m)

  10 passed (2.6m)
```

---

## Technical Explanation

### Why Database Deadlocks Occurred

1. **First test run** → Organisation test fails
2. **Retry mechanism triggers** → `run-with-retry.ts` calls `await runTeardown()`
3. **Playwright starts retry** → `globalSetup.playwright.ts` also calls teardown
4. **Both teardowns run concurrently** → Try to delete same database records
5. **PostgreSQL deadlock** → Circular wait on foreign key constraints

```
Process A: DELETE FROM organisations WHERE user_id=123
Process B: DELETE FROM users WHERE id=123
→ Circular wait on foreign key constraints
→ DeadlockDetected exception
```

### Why Advisory Locks Work

- Database-level synchronisation (works across processes, containers, retries)
- **Blocking behavior** - Second call waits instead of conflicting
- Atomic transactions ensure all-or-nothing operations
- Guaranteed cleanup via `finally` block
- Pure PostgreSQL feature (no external dependencies)

### Why Edge API Fix Was Needed

E2E tests running inside Docker containers cannot reach external APIs due to network isolation. The Flagsmith SDK initialisation was configured to call production Edge API, causing:
- `FetchError: ENOTFOUND edge.api.flagsmith.com`
- Segment tests timing out waiting for SDK response
- Versioning tests failing on flag evaluations

Pointing to local Docker API (`http://flagsmith-api:8000/api/v1/`) resolves this.

---

## Running Tests Locally

### Standard Command
```bash
cd frontend
make test opts="--grep @oss"
```

### With Pre-built Bundle (Faster)
```bash
cd frontend
E2E=1 npm run bundle
SKIP_BUNDLE=1 make test opts="--grep @oss"
```

### With Custom Settings
```bash
# Serial execution
E2E_CONCURRENCY=1 make test opts="--grep @oss"

# Disable retries
E2E_RETRIES=0 make test opts="--grep @oss"

# Specific test file
make test opts="tests/flag-tests.pw.ts"
```

---

## Environment Requirements

- **Node**: v22.18.0 (from `.nvmrc`)
- **Docker**: Any version with Compose support
- **Memory**: 6GB recommended for Docker (Colima: `colima start --memory 6`)
- **macOS/Linux**: Tested and working

---

## For Kyle's PR #6562

### Critical Issues Fixed ✅
1. Database deadlock during teardown
2. Edge API misconfiguration causing 6 test failures
3. Docker Compose compatibility

### Remaining Issues (Not Addressed)
These are out of scope for this fix but should be considered:
- **Firefox-only testing** - Chrome removed from test configuration
- **Browser install** - `test:install` only installs Firefox
- Consider adding Chrome back for cross-browser testing

---

## For Wadii

All setup issues resolved! Here's what was wrong:

1. **Deadlock** - Backend needed advisory locks
2. **Network errors** - Tests were trying to reach production API
3. **Docker compatibility** - Makefile needed auto-detection

Tests now pass reliably at 10/10 (100%). You can run the standard command:
```bash
cd frontend
make test opts="--grep @oss"
```

---

## Verification Steps

### 1. Check for Deadlocks
```bash
docker logs flagsmith-e2e-flagsmith-api-1 | grep -i deadlock
# Should return empty
```

### 2. Check Test Results
```bash
cd frontend
make test opts="--grep @oss"
# Should show: 10 passed (2.6m)
```

### 3. Verify Edge API Usage
```bash
docker logs flagsmith-e2e-frontend-1 | grep "edge.api.flagsmith.com"
# Should return empty (no external API calls)
```

---

## Files Changed Summary

| File | Type | Purpose |
|------|------|---------|
| `api/e2etests/e2e_seed_data.py` | Backend | Added advisory locks |
| `frontend/env/project_e2e.js` | Frontend | Fixed API endpoint |
| `frontend/e2e/run-with-retry.ts` | Frontend | Removed redundant teardown |
| `frontend/Makefile` | Infrastructure | Docker Compose compat |
| `frontend/docker-compose-e2e-tests.yml` | Infrastructure | Added E2E token |

All changes are minimal, targeted, and production-ready.

---

## Next Steps

1. ✅ All fixes applied and tested locally
2. **Share with Kyle** - Suggest incorporating into PR #6562
3. **Consider Chrome** - Add chromium back to playwright.config.ts
4. **CI Verification** - Confirm fixes work in CI environment

## Success Criteria Met ✅

- ✅ Tests run without database deadlock errors
- ✅ Retries work without causing conflicts
- ✅ No external API network errors
- ✅ Teardown always succeeds (no 500 errors)
- ✅ Test pass rate: 10/10 (100%)

---

**This is a complete, tested solution ready for production.**
