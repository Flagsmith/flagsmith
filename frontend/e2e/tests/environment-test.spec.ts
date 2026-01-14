import { test } from '@playwright/test';
import {
  byId,
  click,
  createEnvironment,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers/helpers';
import { PASSWORD, E2E_USER } from '../config';

test('@oss Environment management test', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-0');
  
  log('Create environment');
  await click(page, '#create-env-link');
  await createEnvironment(page, 'Staging');
  
  log('Edit Environment');
  await click(page, '#env-settings-link');
  await setText(page, "[name='env-name']", 'Internal');
  await click(page, '#save-env-btn');
  await waitForElementVisible(page, byId('switch-environment-internal-active'));
  
  log('Delete environment');
  await click(page, '#delete-env-btn');
  await setText(page, "[name='confirm-env-name']", 'Internal');
  await click(page, '#confirm-delete-env-btn');
  await waitForElementVisible(page, byId('features-page'));
});
