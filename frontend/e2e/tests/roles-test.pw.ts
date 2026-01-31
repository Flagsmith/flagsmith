import { test } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_A_ROLE,
  E2E_USER,
  E2E_TEST_IDENTITY,
} from '../config'

test.describe('Roles Tests', () => {
  test('Roles can be created with project and environment permissions @enterprise', async ({ page }) => {
    const {
      click,
      closeModal,
      createFeature,
      createRole,
      deleteFeature,
      gotoTraits,
      login,
      logout,
      waitForElementVisible,
    } = createHelpers(page);

    const rolesProject = 'project-my-test-project-7-role'
    log('Login')
    await login(E2E_USER, PASSWORD)
    await click(byId(rolesProject))
    await createFeature({ name: 'test_feature', value: false })
    log('Go to Roles')
    await click(byId('organisation-link'))
    await click(byId('users-and-permissions'))
    await waitForElementVisible(byId('tab-item-roles'))
    log('Create Role')
    await createRole('test_role', [4])
    log('Add project permissions to the Role')
    await click(byId(`role-0`))
    await click(byId('permissions-tab'))
    await click(byId('permissions-tab'))
    await waitForElementVisible(byId('project-permissions-tab'))
    await click(byId('project-permissions-tab'))
    await click(byId('permissions-my test project 7 role'))
    await click(byId('admin-switch-project'))
    log('Add environment permissions to the Role')
    await waitForElementVisible(byId('environment-permissions-tab'))
    await click(byId('environment-permissions-tab'))
    await click(byId('project-select'))
    await waitForElementVisible(byId('project-select-option-6'))
    await click(byId('project-select-option-6'))
    await click(byId('permissions-development'))
    await click(byId('admin-switch-environment'))
    await closeModal()
    await logout()
    log('Login with the user with a new Role')
    await page.evaluate(() => location.reload());
    await page.waitForTimeout(2000);
    await login(E2E_NON_ADMIN_USER_WITH_A_ROLE, PASSWORD)
    await click(byId(rolesProject))
    log('User with permissions can Handle the Features')
    const flagName = 'test_feature'
    await deleteFeature(flagName)

    log('User with permissions can See the Identities')
    await gotoTraits(E2E_TEST_IDENTITY)
  });
});
