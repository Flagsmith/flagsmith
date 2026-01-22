import { test, expect } from '../test-setup';
import {
  byId,
  click, clickByText, closeModal, createEnvironment,
  createFeature, editRemoteConfig,
  gotoFeature,
  gotoTraits,
  log,
  login, logout, setUserPermission,
  toggleFeature, waitForElementClickable, waitForElementNotClickable, waitForElementNotExist, waitForElementVisible,
  waitForFeatureSwitchClickable,
  createHelpers,
} from '../helpers.playwright';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
  E2E_USER,
} from '../config';

test.describe('Environment Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  log('User can only view project')
  await helpers.click('#project-select-0')
  await expect(page.locator('#project-select-1'))
    .not.toBeVisible({ timeout: 5000 })
  await helpers.logout()

  log('User with permissions can Handle the Features')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await createFeature(page, 0, 'test_feature', false)
  await toggleFeature(page, 'test_feature', true)
  await helpers.logout()

  log('User without permissions cannot create traits')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await gotoTraits(page)
  const createTraitBtn = page.locator(byId('add-trait'))
  await expect(createTraitBtn).toBeDisabled()
  await helpers.logout()

  log('User without permissions cannot see audit logs')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementNotExist(byId('audit-log-link'))
  await helpers.logout()

  log('Create new environment')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.clickByText('My Test Project 6 Env Permission')
  await helpers.click('#create-env-link')
  await createEnvironment(page, 'Production')
  await helpers.logout()
  log('User without permissions cannot see environment')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementVisible(byId('switch-environment-development'))
  await helpers.waitForElementNotExist(byId('switch-environment-production'))
  await helpers.logout()

  log('Grant view environment permission')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_ENVIRONMENT', 'Production', 'environment', 'My Test Project 6 Env Permission' )
  await helpers.logout()
  log('User with permissions can see environment')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementVisible(byId('switch-environment-production'))
  await helpers.waitForElementVisible(byId('switch-environment-production'))
  await helpers.logout()

  log('User with permissions can update feature state')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await createFeature(page, 0,'my_feature',"foo",'A test feature')
  await editRemoteConfig(page, 'my_feature', 'bar')
  await helpers.logout()
  log('User without permission cannot create a segment override')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await gotoFeature(page, 'my_feature')
  await helpers.click(byId('segment_overrides'))
  await waitForElementNotClickable(page, '#update-feature-segments-btn')
  await closeModal(page)
  await helpers.logout()
  log('Grant MANAGE_IDENTITIES permission')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_SEGMENT_OVERRIDES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
  await helpers.logout()
  log('User with permission can create a segment override')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await gotoFeature(page, 'my_feature')
  await helpers.click(byId('segment_overrides'))
  await waitForElementClickable(page, '#update-feature-segments-btn')
  await closeModal(page)
  await helpers.logout()

  log('User without permissions cannot update feature state')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await waitForFeatureSwitchClickable(page, 'test_feature', 'on', true)
  await helpers.click(byId('switch-environment-production'))
  await waitForFeatureSwitchClickable(page, 'test_feature', 'on', false)
  await gotoFeature(page, 'test_feature')
  await waitForElementNotClickable(page, byId('update-feature-btn'))
  await closeModal(page)
  await helpers.logout()

  log('User with permissions can view identities')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementVisible('#users-link')
  await helpers.logout()

  log('User without permissions cannot add user trait')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.click('#users-link')
  await helpers.click(byId('user-item-0'))
  await waitForElementNotClickable(page, byId('add-trait'))
  await helpers.logout()

  log('Grant MANAGE_IDENTITIES permission')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
  await helpers.logout()
  log('User with permissions can add user trait')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.click('#users-link')
  await helpers.click(byId('user-item-0'))
  await waitForElementClickable(page, byId('add-trait'))
  await helpers.logout()


  log('Remove VIEW_IDENTITIES permission')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
  await helpers.logout()
  log('User without permissions cannot view identities')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.click('#users-link')
  await helpers.waitForElementVisible(byId('missing-view-identities'))
  });
});