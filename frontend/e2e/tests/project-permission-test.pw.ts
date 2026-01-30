import { test, expect } from '../test-setup';
import {
  byId,
  log,
  createHelpers,
} from '../helpers.playwright';
import { E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, E2E_USER, PASSWORD, E2E_PROJECT_WITH_PROJECT_PERMISSIONS } from '../config';

test.describe('Project Permission Tests', () => {
  test('Project-level permissions control access to features, environments, audit logs, and segments @enterprise', async ({ page }) => {
    const {
      click,
      clickFeatureAction,
      createEnvironment,
      createFeature,
      getFeatureIndexByName,
      gotoProject,
      gotoSegments,
      login,
      logout,
      setUserPermission,
      toggleFeature,
      waitForElementNotClickable,
      waitForElementNotExist,
      waitForElementVisible,
      waitForFeatureSwitch,
      waitForPageFullyLoaded,
    } = createHelpers(page);

    const PROJECT_NAME = E2E_PROJECT_WITH_PROJECT_PERMISSIONS;

    log('User with VIEW_PROJECT can only see their project')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await waitForElementNotExist('#project-select-1')
    await logout()

    log('User with CREATE_ENVIRONMENT can create an environment')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await createEnvironment('Staging')
    await logout()

    log('User with VIEW_AUDIT_LOG can view the audit log')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await click(byId('audit-log-link'))
    await logout()
    log('Remove VIEW_AUDIT_LOG permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'VIEW_AUDIT_LOG', PROJECT_NAME, 'project' )
    await logout()
    log('User without VIEW_AUDIT_LOG cannot view the audit log')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await waitForElementNotExist('audit-log-link')
    await logout()

    log('User with CREATE_FEATURE can Handle the Features')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await createFeature({ name: 'test_feature', value: false })
    await toggleFeature('test_feature', true)
    await logout()
    log('Remove CREATE_FEATURE permissions')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_FEATURE', PROJECT_NAME, 'project' )
    await logout()
    log('User without CREATE_FEATURE cannot Handle the Features')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await waitForElementNotClickable('#show-create-feature-btn')
    await logout()

    log('User without ADMIN permissions cannot set other users project permissions')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await waitForElementNotExist('#project-settings-link')
    await logout()

    log('Set user as project ADMIN')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', PROJECT_NAME, 'project' )
    await logout()
    log('User with ADMIN permissions can set project settings')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await waitForElementVisible('#project-settings-link')
    await logout()
    log('Remove user as project ADMIN')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', PROJECT_NAME, 'project' )
    await logout()

    log('User without create environment permissions cannot create a new environment')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_ENVIRONMENT', PROJECT_NAME, 'project' )
    await logout()
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await waitForElementNotExist('#create-env-link')
    await logout()

    log('User without DELETE_FEATURE permissions cannot Delete any feature')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await waitForPageFullyLoaded()
    await waitForElementVisible('#features-page')
    await waitForFeatureSwitch('test_feature', 'on')
    await clickFeatureAction('test_feature')
    const featureIndex = await getFeatureIndexByName('test_feature')
    await waitForElementVisible(byId(`feature-remove-${featureIndex}`))
    await expect(page.locator(byId(`feature-remove-${featureIndex}`))).toHaveClass(
      /feature-action__item_disabled/,
    )
    await logout()
    log('Add DELETE_FEATURE permission to user')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'DELETE_FEATURE', PROJECT_NAME, 'project' )
    await logout()
    log('User with permissions can Delete any feature')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await clickFeatureAction('test_feature')
    const featureIndex2 = await getFeatureIndexByName('test_feature')
    await waitForElementVisible(byId(`feature-remove-${featureIndex2}`))
    await expect(page.locator(byId(`feature-remove-${featureIndex2}`))).not.toHaveClass(
      /feature-action__item_disabled/,
    )
    await logout()

    log('User without MANAGE_SEGMENTS permissions cannot Manage Segments')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await gotoSegments()
    const createSegmentBtn = page.locator(byId('show-create-segment-btn'))
    await expect(createSegmentBtn).toBeDisabled()
    await logout()
    log('Add MANAGE_SEGMENTS permission to user')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(
        E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
        'MANAGE_SEGMENTS',
        PROJECT_NAME,
        'project'
    )
    await logout()
    log('User with MANAGE_SEGMENTS permissions can Manage Segments')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await gotoProject(PROJECT_NAME)
    await gotoSegments()
    await expect(createSegmentBtn).not.toBeDisabled()
  });
});