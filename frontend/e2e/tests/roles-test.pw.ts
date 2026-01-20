import { test, expect } from '@playwright/test';
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
  deleteFeature, createRole,
} from '../helpers.pw';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_A_ROLE,
  E2E_USER,
} from '../config'
import { t } from 'testcafe'

test.describe('TestName', () => {
  test('test description', async ({ page }) => {
    const helpers = createHelpers(page);
  const rolesProject = 'project-my-test-project-7-role'
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click(byId(rolesProject))
  await createFeature(0, 'test_feature', false)
  log('Go to Roles')
  await helpers.click(byId('organisation-link'))
  await helpers.click(byId('users-and-permissions'))
  await helpers.waitForElementVisible(byId('tab-item-roles'))
  log('Create Role')
  await createRole('test_role', 0, [4])
  log('Add project permissions to the Role')
  await helpers.click(byId(`role-0`))
  await helpers.click(byId('permissions-tab'))
  await helpers.click(byId('permissions-tab'))
  await helpers.waitForElementVisible(byId('project-permissions-tab'))
  await helpers.click(byId('project-permissions-tab'))
  await helpers.click(byId('permissions-my test project 7 role'))
  await helpers.click(byId('admin-switch-project'))
  log('Add environment permissions to the Role')
  await helpers.waitForElementVisible(byId('environment-permissions-tab'))
  await helpers.click(byId('environment-permissions-tab'))
  await helpers.click(byId('project-select'))
  await helpers.waitForElementVisible(byId('project-select-option-6'))
  await helpers.click(byId('project-select-option-6'))
  await helpers.click(byId('permissions-development'))
  await helpers.click(byId('admin-switch-environment'))
  await closeModal()
  await helpers.logout(t)
  log('Login with the user with a new Role')
  await eval(() => location.reload());
  await wait(2000);
  await helpers.login(E2E_NON_ADMIN_USER_WITH_A_ROLE, PASSWORD)
  await helpers.click(byId(rolesProject))
  log('User with permissions can Handle the Features')
  const flagName = 'test_feature'
  await deleteFeature(0, flagName)

  log('User with permissions can See the Identities')
  await gotoTraits()
  });
});