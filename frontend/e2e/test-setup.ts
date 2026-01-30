import { test, expect } from '@playwright/test';
import { setupBrowserLogging } from './helpers.playwright';

test.beforeEach(async ({ page }) => {
  setupBrowserLogging(page);
});

export { test, expect };
