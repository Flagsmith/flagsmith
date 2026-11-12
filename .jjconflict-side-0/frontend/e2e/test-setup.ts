import { test as base, expect } from '@playwright/test';
import { setupBrowserLogging } from './helpers';

// Third-party widgets (e.g. the HubSpot chat bubble) can overlay UI elements
// and intercept pointer events, so block them at the network level.
const THIRD_PARTY_SCRIPT_HOSTS =
  /(hubspot|hs-scripts|hs-analytics|hs-banner|hsforms|usemessages|google-analytics)\./;

const test = base.extend<{ e2eSetup: void }>({
  e2eSetup: [async ({ context, page }, use) => {
    await context.route(
      (url) => THIRD_PARTY_SCRIPT_HOSTS.test(url.hostname),
      (route) => route.abort(),
    );
    setupBrowserLogging(page);
    await use();
  }, { auto: true }],
});

export { test, expect };
