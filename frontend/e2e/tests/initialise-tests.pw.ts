import { test } from '../test-setup';
import {
  byId,
  createHelpers,
  getFlagsmith,
  log,
} from '../helpers.playwright';
import { E2E_SIGN_UP_USER, PASSWORD } from '../config';

test.describe('Signup', () => {
  test('Create Organisation and Project @oss', async ({ page }) => {
    const { addErrorLogging, click, logout, setText, waitForElementVisible } = createHelpers(page);
    const flagsmith = await getFlagsmith();

    // Add error logging
    await addErrorLogging();

    // Navigate to signup page
    await page.goto('/');

    log('Create Organisation');
    await click(byId('jsSignup'));
    // Wait for firstName field to be visible after modal opens
    await waitForElementVisible(byId('firstName'));
    await setText(byId('firstName'), 'Bullet');
    await setText(byId('lastName'), 'Train');
    await setText(byId('email'), E2E_SIGN_UP_USER);
    await setText(byId('password'), PASSWORD);
    await click(byId('signup-btn'));
    // Wait for navigation and form to load after signup
    await page.waitForURL(/\/create/, { timeout: 20000 });
    await waitForElementVisible('[name="orgName"]');
    await setText('[name="orgName"]', 'Flagsmith Ltd 0');
    await click('#create-org-btn');

    if (flagsmith.hasFeature('integration_onboarding')) {
      await click(byId('integration-0'));
      await click(byId('integration-1'));
      await click(byId('integration-2'));
      await click(byId('submit-integrations'));
    }
    await click(byId('create-project'));

    log('Create Project');
    await click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await click(byId('create-project-btn'));
    await waitForElementVisible(byId('features-page'));

    log('Hide disabled flags');
    await click('#project-link');
    await click('#project-settings-link');
    await click(byId('js-sdk-settings'));
    await click(byId('js-hide-disabled-flags'));
    await setText(byId('js-project-name'), 'My Test Project');
    await click(byId('js-confirm'));

    // Logout after test
    await logout();
  });
});