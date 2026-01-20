import { test } from '@playwright/test';
import { createHelpers, getFlagsmith } from './helpers.pw';

// Import all test files
import './tests/initialise-tests.pw';
import './tests/segment-test.pw';
import './tests/flag-tests.pw';
import './tests/invite-test.pw';
import './tests/environment-test.pw';
import './tests/project-test.pw';
import './tests/organisation-test.pw';
import './tests/versioning-tests.pw';
import './tests/organisation-permission-test.pw';
import './tests/project-permission-test.pw';
import './tests/environment-permission-test.pw';
import './tests/roles-test.pw';

// Global test configuration
test.beforeEach(async ({ page }) => {
  const helpers = createHelpers(page);

  // Add error logging to all pages
  await helpers.addErrorLogging();

  // Wait for React if needed (you may need to implement a custom wait for your React app)
  // This depends on your app's specific loading behavior
  await page.waitForLoadState('networkidle');
});

test.afterEach(async ({ page }, testInfo) => {
  // Take screenshot on failure
  if (testInfo.status === 'failed') {
    await page.screenshot({
      path: `test-results/screenshots/${testInfo.title}-failure.png`,
      fullPage: true
    });
  }

  // Log console errors if any
  const helpers = createHelpers(page);
  const consoleErrors = await helpers.getConsoleMessages();
  if (consoleErrors.length > 0) {
    console.log('Console errors:', consoleErrors);
  }
});

// Helper to filter tests based on metadata
export function filterTests(testFn: any, metadata: { category?: string; autoLogout?: boolean; skipEnterprise?: boolean }) {
  const filterString = process.env.META_FILTER || '';
  const conditions = filterString.split(',').map(pair => {
    const [key, value] = pair.split('=');
    return { key, value };
  });

  if (conditions.length === 0 || !filterString) {
    return testFn;
  }

  const isEnterpriseRun = conditions.some(({ key, value }) =>
    key === 'category' && value === 'enterprise'
  );

  if (isEnterpriseRun && metadata.skipEnterprise) {
    return test.skip;
  }

  const shouldRun = conditions.some(({ key, value }) => {
    return metadata[key as keyof typeof metadata]?.toString() === value;
  });

  return shouldRun ? testFn : test.skip;
}