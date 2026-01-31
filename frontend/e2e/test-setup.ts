import { test, expect } from '@playwright/test';
import { setupBrowserLogging } from './helpers';

test.beforeEach(async ({ page }) => {
  setupBrowserLogging(page);
});

export { test, expect };
