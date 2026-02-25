import { test, expect } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import { PASSWORD, E2E_USER, E2E_TEST_PROJECT } from '../config'

test.describe('Environment Tests', () => {
  test('Environments can be created, renamed, and deleted @oss', async ({ page }) => {
    const {
      click,
      createEnvironment,
      gotoProject,
      login,
      setText,
      waitForElementVisible,
    } = createHelpers(page);

    log('Login')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)
    await waitForElementVisible(byId('switch-environment-development'))
    log('Create environment')
    await click('#create-env-link')
    await createEnvironment('Staging')
    log('Edit Environment')
    await click('#env-settings-link')
    await setText("[name='env-name']", 'Internal')
    await click('#save-env-btn')
    await waitForElementVisible(byId('switch-environment-internal-active'))
    log('Delete environment')
    await click('#delete-env-btn')
    await setText("[name='confirm-env-name']", 'Internal')
    await click('#confirm-delete-env-btn')
    await waitForElementVisible(byId('features-page'))
  });
});