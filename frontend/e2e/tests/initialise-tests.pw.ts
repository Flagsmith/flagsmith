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
    const helpers = createHelpers(page);
    const flagsmith = await getFlagsmith();

    // Add error logging
    await helpers.addErrorLogging();

    // Navigate to signup page
    await page.goto('/');

    log('Create Organisation');
    await helpers.click(byId('jsSignup'));
    // Wait for firstName field to be visible after modal opens
    await helpers.waitForElementVisible(byId('firstName'));
    await helpers.setText(byId('firstName'), 'Bullet');
    await helpers.setText(byId('lastName'), 'Train');
    await helpers.setText(byId('email'), E2E_SIGN_UP_USER);
    await helpers.setText(byId('password'), PASSWORD);
    await helpers.click(byId('signup-btn'));
    // Wait for navigation and form to load after signup
    await page.waitForURL(/\/create/, { timeout: 20000 });
    await helpers.waitForElementVisible('[name="orgName"]');
    await helpers.setText('[name="orgName"]', 'Flagsmith Ltd 0');
    await helpers.click('#create-org-btn');

    if (flagsmith.hasFeature('integration_onboarding')) {
      await helpers.click(byId('integration-0'));
      await helpers.click(byId('integration-1'));
      await helpers.click(byId('integration-2'));
      await helpers.click(byId('submit-integrations'));
    }
    await helpers.click(byId('create-project'));

    log('Create Project');
    await helpers.click(byId('create-first-project-btn'));
    await helpers.setText(byId('projectName'), 'My Test Project');
    await helpers.click(byId('create-project-btn'));
    await helpers.waitForElementVisible(byId('features-page'));

    log('Hide disabled flags');
    await helpers.click('#project-link');
    await helpers.click('#project-settings-link');
    await helpers.click(byId('js-sdk-settings'));
    await helpers.click(byId('js-hide-disabled-flags'));
    await helpers.setText(byId('js-project-name'), 'My Test Project');
    await helpers.click(byId('js-confirm'));

    // Logout after test
    await helpers.logout();
  });
});