import { test, expect } from '../test-setup';
import {
  byId,
  log,
  createHelpers,
} from '../helpers';
import { E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, E2E_USER, PASSWORD } from '../config';

test.describe('Project Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const {
      click,
      clickFeatureAction,
      createEnvironment,
      createFeature,
      getFeatureIndexByName,
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

    log('User with VIEW_PROJECT can only see their project')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await waitForElementNotExist('#project-select-1')
    await logout()

    log('User with CREATE_ENVIRONMENT can create an environment')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await createEnvironment('Staging')
    await logout()

    log('User with VIEW_AUDIT_LOG can view the audit log')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await click(byId('audit-log-link'))
    await logout()
    log('Remove VIEW_AUDIT_LOG permission')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'VIEW_AUDIT_LOG', 'My Test Project 5 Project Permission', 'project' )
    await logout()
    log('User without VIEW_AUDIT_LOG cannot view the audit log')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementNotExist('audit-log-link')
    await logout()

    log('User with CREATE_FEATURE can Handle the Features')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await createFeature({ name: 'test_feature', value: false })
    await toggleFeature('test_feature', true)
    await logout()
    log('Remove CREATE_FEATURE permissions')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_FEATURE', 'My Test Project 5 Project Permission', 'project' )
    await logout()
    log('User without CREATE_FEATURE cannot Handle the Features')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementNotClickable('#show-create-feature-btn')
    await logout()

    log('User without ADMIN permissions cannot set other users project permissions')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await waitForElementNotExist('#project-settings-link')
    await logout()

    log('Set user as project ADMIN')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project' )
    await logout()
    log('User with ADMIN permissions can set project settings')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementVisible('#project-settings-link')
    await logout()
    log('Remove user as project ADMIN')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project' )
    await logout()

    log('User without create environment permissions cannot create a new environment')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_ENVIRONMENT', 'My Test Project 5 Project Permission', 'project' )
    await logout()
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await waitForElementNotExist('#create-env-link')
    await logout()

    log('User without DELETE_FEATURE permissions cannot Delete any feature')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
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
    await setUserPermission(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'DELETE_FEATURE', 'My Test Project 5 Project Permission', 'project' )
    await logout()
    log('User with permissions can Delete any feature')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await clickFeatureAction('test_feature')
    const featureIndex2 = await getFeatureIndexByName('test_feature')
    await waitForElementVisible(byId(`feature-remove-${featureIndex2}`))
    await expect(page.locator(byId(`feature-remove-${featureIndex2}`))).not.toHaveClass(
      /feature-action__item_disabled/,
    )
    await logout()

    log('User without MANAGE_SEGMENTS permissions cannot Manage Segments')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await gotoSegments()
    const createSegmentBtn = page.locator(byId('show-create-segment-btn'))
    await expect(createSegmentBtn).toBeDisabled()
    await logout()
    log('Add MANAGE_SEGMENTS permission to user')
    await login(E2E_USER, PASSWORD)
    await setUserPermission(
        E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
        'MANAGE_SEGMENTS',
        'My Test Project 5 Project Permission',
        'project'
    )
    await logout()
    log('User with MANAGE_SEGMENTS permissions can Manage Segments')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await click('#project-select-0')
    await gotoSegments()
    await expect(createSegmentBtn).not.toBeDisabled()
  });
});
