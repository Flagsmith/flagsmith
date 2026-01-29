import { test, expect } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import { PASSWORD, E2E_USER } from '../config'

test.describe('Environment Tests', () => {
  test('test description @oss', async ({ page }) => {
    const {
      click,
      createEnvironment,
      login,
      setText,
      waitForElementVisible,
    } = createHelpers(page);

    log('Login')
    await login(E2E_USER, PASSWORD)
    await click('#project-select-0')
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
