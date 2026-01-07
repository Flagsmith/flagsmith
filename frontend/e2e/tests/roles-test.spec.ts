import { test } from '@playwright/test';
import {
  byId,
  click,
  createFeature,
  log,
  login,
  setText,
  waitForElementVisible,
  closeModal,
  logout,
  gotoTraits,
  deleteFeature,
  createRole,
} from '../helpers/helpers';

import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_A_ROLE,
  E2E_USER,
} from '../config';

test('@enterprise Roles and permissions test', async ({ page }) => {
  const rolesProject = 'project-my-test-project-7-role';

  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, byId(rolesProject));
  await createFeature(page, 0, 'test_feature', false);

  log('Go to Roles');
  await click(page, byId('organisation-link'));
  await click(page, byId('users-and-permissions'));
  await waitForElementVisible(page, byId('tab-item-roles'));

  log('Create Role');
  await createRole(page, 'test_role', 0, [4]);

  log('Add project permissions to the Role');
  await click(page, byId(`role-0`));
  await click(page, byId('permissions-tab'));
  await click(page, byId('permissions-tab'));
  await waitForElementVisible(page, byId('project-permissions-tab'));
  await click(page, byId('project-permissions-tab'));
  await click(page, byId('permissions-my test project 7 role'));
  await click(page, byId('admin-switch-project'));

  log('Add environment permissions to the Role');
  await waitForElementVisible(page, byId('environment-permissions-tab'));
  await click(page, byId('environment-permissions-tab'));
  await click(page, byId('project-select'));
  await waitForElementVisible(page, byId('project-select-option-6'));
  await click(page, byId('project-select-option-6'));
  await click(page, byId('permissions-development'));
  await click(page, byId('admin-switch-environment'));
  await closeModal(page);

  await logout(page);

  log('Login with the user with a new Role');
  await page.reload();
  await page.waitForTimeout(2000);
  await login(page, E2E_NON_ADMIN_USER_WITH_A_ROLE, PASSWORD);
  await click(page, byId(rolesProject));

  log('User with permissions can Handle the Features');
  const flagName = 'test_feature';
  await deleteFeature(page, 0, flagName);

  log('User with permissions can See the Identities');
  await gotoTraits(page);
});
