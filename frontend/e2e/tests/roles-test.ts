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
} from '../helpers.cafe'
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_A_ROLE,
  E2E_USER,
} from '../config'
import { t } from 'testcafe'

export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-6')
  await createFeature(0, 'test_feature', false)
  log('Go to Roles')
  await click(byId('org-settings-link'))
  await click(byId('users-and-permissions'))
  await waitForElementVisible(byId('tab-item-roles'))
  await click(byId('tab-item-roles'))
  await click(byId('btn-create-role-modal'))
  const roleName = 'test_role'
  await setText(byId('role-name'), roleName)
  log('Add permissions to the Roles')
  await click(byId('update-role-btn'))
  await click(byId('role-0'))
  await click(byId('members-tab'))
  await click(byId('assigned-users'))
  await click(byId('assignees-list-item-4'))
  await click(byId('permissions-tab'))
  await click(byId('permissions-tab'))
  await waitForElementVisible(byId('project-permissions-tab'))
  await click(byId('project-permissions-tab'))
  await waitForElementVisible(byId('permissions-list-item-project-6'))
  await click(byId('permissions-list-item-project-6'))
  await waitForElementVisible(byId('admin-switch-project'))
  await click(byId('permission-switch-project-0'))
  await click(byId('permission-switch-project-2'))
  await click(byId('permission-switch-project-4'))
  await waitForElementVisible(byId('environment-permissions-tab'))
  await click(byId('environment-permissions-tab'))
  await click(byId('project-select'))
  await waitForElementVisible(byId('project-select-option-6'))
  await click(byId('project-select-option-6'))
  await waitForElementVisible(byId('permissions-list-item-environment-0'))
  await click(byId('permissions-list-item-environment-0'))
  await click(byId('permissions-list-item-environment-0'))
  await click(byId('permission-switch-environment-0'))
  await click(byId('permission-switch-environment-2'))
  await click(byId('permission-switch-environment-3'))
  await click(byId('permission-switch-environment-4'))
  await click(byId('permission-switch-environment-5'))
  await click(byId('permission-switch-environment-6'))
  await closeModal()
  await logout(t)
  log('Login with the user with a new Role')
  await t.eval(() => location.reload());
  await t.wait(2000);
  await login(E2E_NON_ADMIN_USER_WITH_A_ROLE, PASSWORD)
  await click('#project-select-0')
  log('User with permissions can Handle the Features')
  const flagName = 'test_feature'
  await deleteFeature(0, flagName)

  log('User with permissions can See the Identities')
  await gotoTraits()
}
