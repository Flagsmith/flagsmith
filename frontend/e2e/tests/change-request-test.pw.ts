import { test, expect } from '../test-setup'
import { byId, getFlagsmith, log, createHelpers } from '../helpers'
import {
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
  E2E_TEST_PROJECT,
  E2E_USER,
  PASSWORD,
} from '../config'

test.describe('Change Request Tests', () => {
  test('Change requests can be created, approved, and published with 4-eyes approval @enterprise', async ({
    page,
  }) => {
    const {
      assertChangeRequestCount,
      approveChangeRequest,
      assertInputValue,
      closeModal,
      createChangeRequest,
      createEnvironment,
      createRemoteConfig,
      enableChangeRequests,
      gotoChangeRequests,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      login,
      logout,
      openChangeRequest,
      parseTryItResults,
      publishChangeRequest,
      setText,
      setUserPermission,
      waitForElementVisible,
    } = createHelpers(page)

    const flagsmith = await getFlagsmith()
    const hasChangeRequests = flagsmith.hasFeature('segment_change_requests')

    if (!hasChangeRequests) {
      log('Skipping change request test, feature not enabled.')
      test.skip()
      return
    }

    const projectName = E2E_TEST_PROJECT
    const environmentName = 'CR_Test_Env'
    const featureName = 'cr_test_feature'

    log('Login as admin')
    await login(E2E_USER, PASSWORD)

    log('Navigate to test project')
    await gotoProject(projectName)

    log('Create test environment')
    await page.click('text="Create Environment"')
    await createEnvironment(environmentName)

    log('Enable change requests for test environment')
    await enableChangeRequests(1)

    log('Create initial feature')
    await createRemoteConfig({
      name: featureName,
      value: 'initial_value',
    })

    log('Verify initial value via API')
    await page.click('#try-it-btn')
    let json = await parseTryItResults()
    expect(json[featureName].value).toBe('initial_value')

    log('Create change request by editing feature value')
    await gotoFeatures()
    await gotoFeature(featureName)
    await setText(byId('featureValue'), 'updated_value')

    await createChangeRequest(
      'Update feature value',
      'Updating value from initial_value to updated_value',
    )

    log('Verify change request was created')
    await closeModal()

    log('Verify value has NOT changed yet (change request not approved)')
    await page.click('#try-it-btn')
    json = await parseTryItResults()
    expect(json[featureName].value).toBe('initial_value') // Still old value

    log('Grant approver project ADMIN permission')
    await page.click('a:has-text("Bullet Train Ltd")')
    await setUserPermission(
      E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
      'ADMIN',
      projectName,
      'project'
    )

    log('Logout and login as approver')
    await logout()
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)

    log('Navigate to project')
    await gotoProject(projectName)

    log(`Switch to ${environmentName} environment`)
    await page.click(`text="${environmentName}"`)

    log('Go to change requests')
    await gotoChangeRequests()

    log('Open change request')
    await openChangeRequest(0)

    log('Approve change request')
    await approveChangeRequest()

    log('Publish change request')
    await publishChangeRequest()

    log('Close modal')
    await closeModal()

    log('Verify value has NOW changed (change request published)')
    await gotoFeatures()
    await gotoFeature(featureName)
    await assertInputValue(byId('featureValue'), 'updated_value')
    await closeModal()

    log('Verify value via API')
    await page.click('#try-it-btn')
    json = await parseTryItResults()
    expect(json[featureName].value).toBe('updated_value')

    log('Verify change request is no longer in list')
    await gotoChangeRequests()
    await assertChangeRequestCount(0)

    log('Change request test completed successfully')
  })
})
