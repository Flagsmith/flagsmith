import { test as base, expect } from '@playwright/test';
import { setupBrowserLogging } from './helpers';

const test = base.extend<{ e2eSetup: void }>({
  e2eSetup: [async ({ page }, use) => {
    setupBrowserLogging(page);
    await use();
  }, { auto: true }],
});

export { test, expect };
