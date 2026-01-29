import { test as base } from '@playwright/test';
import { setupBrowserLogging } from './helpers';

// Extend base test to automatically setup browser logging
export const test = base.extend({
  page: async ({ page }, use) => {
    // Setup logging before each test
    setupBrowserLogging(page);

    // Use the page in the test
    await use(page);
  },
});

export { expect } from '@playwright/test';
