# TestCafe to Playwright Migration Guide

## Overview
This document outlines the migration from TestCafe to Playwright for E2E testing with minimal changes to the file structure.

## Key Changes

### 1. Test Framework
- **Before**: TestCafe
- **After**: Playwright Test (@playwright/test)

### 2. File Structure (Preserved)
```
e2e/
├── tests/
│   ├── *.ts (original TestCafe tests)
│   └── *.pw.ts (new Playwright tests)
├── helpers.cafe.ts (original)
├── helpers.pw.ts (new Playwright helpers)
├── config.ts (unchanged)
├── global-setup.ts (new)
├── global-teardown.ts (new)
└── playwright.config.ts (replaces .testcaferc.js)
```

### 3. Test File Naming Convention
- TestCafe tests: `*.ts`
- Playwright tests: `*.pw.ts`
- This allows both frameworks to coexist during the transition

### 4. Configuration Files
- **TestCafe**: `.testcaferc.js`
- **Playwright**: `playwright.config.ts`

### 5. Test Scripts in package.json

| Command | Description |
|---------|-------------|
| `npm test` | Run all Playwright tests |
| `npm run test:dev` | Run tests in headed mode with E2E_DEV=true |
| `npm run test:devlocal` | Run tests locally with E2E_LOCAL=true |
| `npm run test:ui` | Open Playwright UI mode |
| `npm run test:headed` | Run tests in headed browser |
| `npm run test:install` | Install Playwright browsers |

### 6. Helper Functions Migration

#### TestCafe Pattern:
```typescript
await click(selector);
await setText(selector, text);
await t.expect(element.exists).ok();
```

#### Playwright Pattern:
```typescript
const helpers = createHelpers(page);
await helpers.click(selector);
await helpers.setText(selector, text);
await expect(page.locator(selector)).toBeVisible();
```

### 7. Test Structure Changes

#### TestCafe:
```typescript
import { test, fixture } from 'testcafe';

fixture`Test Suite`.page`${url}`;

test('Test name', async (t) => {
  // test code
});
```

#### Playwright:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Test Suite', () => {
  test('Test name', async ({ page }) => {
    const helpers = createHelpers(page);
    // test code
  });
});
```

### 8. Key API Differences

| TestCafe | Playwright |
|----------|------------|
| `Selector(selector)` | `page.locator(selector)` |
| `t.click()` | `page.click()` or `helpers.click()` |
| `t.typeText()` | `page.fill()` or `helpers.setText()` |
| `t.expect().ok()` | `expect().toBeVisible()` |
| `t.wait(ms)` | `page.waitForTimeout(ms)` |
| `t.navigateTo(url)` | `page.goto(url)` |

### 9. Environment Variables
All existing environment variables are preserved:
- `E2E_DEV`
- `E2E_LOCAL`
- `E2E_CONCURRENCY`
- `E2E_USER`
- `E2E_PASS`
- `E2E_TEST_TOKEN`
- `META_FILTER`

### 10. Features Maintained
- Firefox browser support (headless/headed based on E2E_DEV)
- Video recording on failure
- Screenshot capture on failure
- Parallel test execution
- Test filtering by metadata
- Global setup/teardown
- Error logging

## Migration Steps

1. **Install Playwright**:
   ```bash
   npm install --save-dev @playwright/test playwright
   ```

2. **Install browsers**:
   ```bash
   npx playwright install firefox
   ```

3. **Run tests**:
   ```bash
   npm test
   ```

## Gradual Migration Strategy

1. Both TestCafe and Playwright tests can coexist during migration
2. Migrate tests incrementally by creating `.pw.ts` versions
3. Once all tests are migrated, remove TestCafe files and dependencies
4. Update CI/CD pipelines to use Playwright commands

## Benefits of Migration

1. **Better performance**: Playwright is generally faster
2. **Modern API**: More intuitive async/await patterns
3. **Better debugging**: UI mode, trace viewer, and better error messages
4. **Active development**: Playwright is actively maintained by Microsoft
5. **Better TypeScript support**: First-class TypeScript support
6. **Cross-browser testing**: Easy to add Chrome, Safari support later

## Notes

- The migration script (`migrate-tests.js`) provides basic conversion but manual review is required
- Test selectors and logic remain the same
- Helper functions are wrapped to maintain similar API
- All test metadata and filtering capabilities are preserved