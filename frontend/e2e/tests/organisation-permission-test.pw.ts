import { test, expect } from '@playwright/test';
import {
  byId,
  click, clickByText,
  closeModal,
  log,
  login, logout,
  setText, waitForElementClickable, waitForElementNotClickable,
  waitForElementVisible,
  createHelpers,
} from '../helpers.playwright';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS,
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
} from '../config';

test.describe('Organisation Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS, PASSWORD)
  log('User without permissions cannot see any Project')
  await expect(page.locator('#project-select-0')).not.toBeVisible()
  log('User with permissions can Create a Project')
  await waitForElementClickable(page,  byId('create-first-project-btn'))

  log('User can manage groups')
  await helpers.click(byId('users-and-permissions'))
  await helpers.clickByText('Groups')
  await waitForElementClickable(page, "#btn-invite-groups")
  await helpers.logout()
  log('Login as project user')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  log('User cannot manage users or groups')
  await helpers.click(byId('users-and-permissions'))
  await helpers.clickByText('Groups')
  await waitForElementNotClickable(page, "#btn-invite-groups")
  });
});