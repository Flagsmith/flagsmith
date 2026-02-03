import { test, expect } from '@playwright/test';
import { setupBrowserLogging } from './helpers';

test.beforeEach(async ({ page }) => {
  // Inject E2E flag before page loads
  await page.addInitScript(() => {
    window.E2E = true;
  });
  setupBrowserLogging(page);
});

export { test, expect };
