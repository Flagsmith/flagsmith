import { test, expect } from '../test-setup';
import {
  byId,
  click,
  createEnvironment,
  createFeature,
  gotoSegments,
  log,
  login,
  logout,
  setUserPermission,
  toggleFeature,
  waitForElementNotClickable,
  waitForElementNotExist,
  waitForElementVisible,
  waitForPageFullyLoaded,
  createHelpers,
} from '../helpers.playwright';
import { E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, E2E_USER, PASSWORD } from '../config';

test.describe('Project Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const helpers = createHelpers(page);

  log('User with VIEW_PROJECT can only see their project')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.waitForElementNotExist('#project-select-1')
  await helpers.logout()

  log('User with CREATE_ENVIRONMENT can create an environment')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await createEnvironment(page, 'Staging')
  await helpers.logout()

  log('User with VIEW_AUDIT_LOG can view the audit log')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.click(byId('audit-log-link'))
  await helpers.logout()
  log('Remove VIEW_AUDIT_LOG permission')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'VIEW_AUDIT_LOG', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()
  log('User without VIEW_AUDIT_LOG cannot view the audit log')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementNotExist('audit-log-link')
  await helpers.logout()

  log('User with CREATE_FEATURE can Handle the Features')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await createFeature(page, 0, 'test_feature', false)
  await toggleFeature(page, 0, true)
  await helpers.logout()
  log('Remove CREATE_FEATURE permissions')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_FEATURE', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()
  log('User without CREATE_FEATURE cannot Handle the Features')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await waitForElementNotClickable(page, '#show-create-feature-btn')
  await helpers.logout()

  log('User without ADMIN permissions cannot set other users project permissions')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.waitForElementNotExist('#project-settings-link')
  await helpers.logout()

  log('Set user as project ADMIN')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()
  log('User with ADMIN permissions can set project settings')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementVisible('#project-settings-link')
  await helpers.logout()
  log('Remove user as project ADMIN')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()

  log('User without create environment permissions cannot create a new environment')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_ENVIRONMENT', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.waitForElementNotExist('#create-env-link')
  await helpers.logout()

  log('User without DELETE_FEATURE permissions cannot Delete any feature')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await waitForPageFullyLoaded(page)
  await waitForElementVisible(page, '#features-page')
  await waitForElementVisible(page, byId('feature-switch-0-off'))
  await helpers.click(byId('feature-action-0'))
  await helpers.waitForElementVisible(byId('feature-remove-0'))
  await expect(page.locator(byId('feature-remove-0'))).toHaveClass(
    /feature-action__item_disabled/,
  )
  await helpers.logout()
  log('Add DELETE_FEATURE permission to user')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'DELETE_FEATURE', 'My Test Project 5 Project Permission', 'project' )
  await helpers.logout()
  log('User with permissions can Delete any feature')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.click(byId('feature-action-0'))
  await helpers.waitForElementVisible(byId('feature-remove-0'))
  await expect(page.locator(byId('feature-remove-0'))).not.toHaveClass(
    /feature-action__item_disabled/,
  )
  await helpers.logout()

  log('User without MANAGE_SEGMENTS permissions cannot Manage Segments')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.gotoSegments()
  const createSegmentBtn = page.locator(byId('show-create-segment-btn'))
  await expect(createSegmentBtn).toBeDisabled()
  await helpers.logout()
  log('Add MANAGE_SEGMENTS permission to user')
  await helpers.login(E2E_USER, PASSWORD)
  await setUserPermission(page, 
      E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
      'MANAGE_SEGMENTS',
      'My Test Project 5 Project Permission',
      'project'
  )
  await helpers.logout()
  log('User with MANAGE_SEGMENTS permissions can Manage Segments')
  await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await helpers.click('#project-select-0')
  await helpers.gotoSegments()
  await expect(createSegmentBtn).not.toBeDisabled()
  });
});