import { test, expect } from '@playwright/test';
import {
  byId,
  click,
  clickByText,
  closeModal,
  log,
  login,
  logout,
  setText,
  waitForElementClickable,
  waitForElementNotClickable,
  waitForElementVisible,
} from '../helpers/helpers';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS,
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
} from '../config';

test('@enterprise Organization permissions test', async ({ page }) => {
  log('Login');
  await login(page, E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS, PASSWORD);
  
  log('User without permissions cannot see any Project');
  await expect(page.locator('#project-select-0')).not.toBeVisible();
  
  log('User with permissions can Create a Project');
  await waitForElementClickable(page, byId('create-first-project-btn'));

  log('User can manage groups');
  await click(page, byId('users-and-permissions'));
  await clickByText(page, 'Groups');
  await waitForElementClickable(page, "#btn-invite-groups");
  await logout(page);
  
  log('Login as project user');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  
  log('User cannot manage users or groups');
  await click(page, byId('users-and-permissions'));
  await clickByText(page, 'Groups');
  await waitForElementNotClickable(page, "#btn-invite-groups");
});
