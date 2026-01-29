import { test, expect } from '../test-setup';
import {
  byId,
  log,
  createHelpers,
} from '../helpers';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
  E2E_USER,
  E2E_TEST_IDENTITY,
} from '../config';

test.describe('Environment Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const {
      click,
      clickByText,
      closeModal,
      createEnvironment,
      createFeature,
      editRemoteConfig,
      gotoFeature,
      gotoTraits,
      login,
      logout,
      setUserPermission,
      toggleFeature,
      waitForElementClickable,
      waitForElementNotClickable,
      waitForElementNotExist,
      waitForElementVisible,
      waitForFeatureSwitchClickable,
    } = createHelpers(page);

    log('Login')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    log('User can only view project')
    await click('#project-select-0')
    await expect(page.locator('#project-select-1'))
      .not.toBeVisible({ timeout: 5000 })
    await logout()

    log('User with permissions can Handle the Features')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await createFeature({ name: 'test_feature', value: false })
    await toggleFeature('test_feature', true)
    await logout()

    log('User without permissions cannot create traits')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await gotoTraits(E2E_TEST_IDENTITY)
    const createTraitBtn = page.locator(byId('add-trait'))
    await expect(createTraitBtn).toBeDisabled()
    await logout()

    log('User without permissions cannot see audit logs')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementNotExist(byId('audit-log-link'))
    await logout()

    log('Create new environment')
    await login(E2E_USER, PASSWORD)
    await clickByText('My Test Project 6 Env Permission')
    await click('#create-env-link')
    await createEnvironment('Production')
    await logout()
    log('User without permissions cannot see environment')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementVisible(byId('switch-environment-development'))
    await waitForElementNotExist(byId('switch-environment-production'))
    await logout()

    log('Grant view environment permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_ENVIRONMENT', 'Production', 'environment', 'My Test Project 6 Env Permission' )
    await logout()
    log('User with permissions can see environment')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementVisible(byId('switch-environment-production'))
    await waitForElementVisible(byId('switch-environment-production'))
    await logout()

    log('User with permissions can update feature state')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await createFeature({ name: 'my_feature', value: 'foo', description: 'A test feature' })
    await editRemoteConfig('my_feature', 'bar')
    await logout()
    log('User without permission cannot create a segment override')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await gotoFeature('my_feature')
    await click(byId('segment_overrides'))
    await waitForElementNotClickable('#update-feature-segments-btn')
    await closeModal()
    await logout()
    log('Grant MANAGE_IDENTITIES permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_SEGMENT_OVERRIDES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
    await logout()
    log('User with permission can create a segment override')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await gotoFeature('my_feature')
    await click(byId('segment_overrides'))
    await waitForElementClickable('#update-feature-segments-btn')
    await closeModal()
    await logout()

    log('User without permissions cannot update feature state')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForFeatureSwitchClickable('test_feature', 'on', true)
    await click(byId('switch-environment-production'))
    await waitForFeatureSwitchClickable('test_feature', 'off', false)
    await gotoFeature('test_feature')
    await waitForElementNotClickable(byId('update-feature-btn'))
    await closeModal()
    await logout()

    log('User with permissions can view identities')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementVisible('#users-link')
    await logout()

    log('User without permissions cannot add user trait')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await click('#users-link')
    await page.locator('[data-test^="user-item-"]').filter({ hasText: E2E_TEST_IDENTITY }).first().click()
    await waitForElementNotClickable(byId('add-trait'))
    await logout()

    log('Grant MANAGE_IDENTITIES permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
    await logout()
    log('User with permissions can add user trait')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await click('#users-link')
    await page.locator('[data-test^="user-item-"]').filter({ hasText: E2E_TEST_IDENTITY }).first().click()
    await waitForElementClickable(byId('add-trait'))
    await logout()


    log('Remove VIEW_IDENTITIES permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission' )
    await logout()
    log('User without permissions cannot view identities')
    await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await click('#users-link')
    await waitForElementVisible(byId('missing-view-identities'))
  });
});
