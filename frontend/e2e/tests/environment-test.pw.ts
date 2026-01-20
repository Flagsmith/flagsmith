import { test, expect } from '@playwright/test';
import {
  byId,
  click,
  createEnvironment,
  log,
  login,
  setText,
  waitForElementVisible,
  createHelpers,
} from '../helpers.playwright';
import { PASSWORD, E2E_USER } from '../config'

test.describe('Environment Tests', () => {
  test('test description', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-0')
  log('Create environment')
  await helpers.click('#create-env-link')
  await createEnvironment(page, 'Staging')
  log('Edit Environment')
  await helpers.click('#env-settings-link')
  await helpers.setText("[name='env-name']", 'Internal')
  await helpers.click('#save-env-btn')
  await helpers.waitForElementVisible(byId('switch-environment-internal-active'))
  log('Delete environment')
  await helpers.click('#delete-env-btn')
  await helpers.setText("[name='confirm-env-name']", 'Internal')
  await helpers.click('#confirm-delete-env-btn')
  await helpers.waitForElementVisible(byId('features-page'))
  });
});