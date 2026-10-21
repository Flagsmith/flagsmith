import { test, expect } from '../test-setup'
import { byId, getFlagsmith, log, createHelpers, visualSnapshot } from '../helpers'
import {
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
  E2E_TEST_PROJECT,
  E2E_USER,
  PASSWORD,
} from '../config'

test.describe('Change Request Tests', () => {
  test('Change requests can be created, approved, and published with four-eyes approval @enterprise', async ({
    page,
  }, testInfo) => {
    const {
      featureValueField,
      assertChangeRequestCount,
      approveChangeRequest,
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
      publishChangeRequest,
      tryItExpect,
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
    // New environment + feature needs more time for edge API propagation
    await tryItExpect(featureName, 'value', 'initial_value', 30)

    log('Create change request by editing feature value')
    await gotoFeatures()
    await gotoFeature(featureName)
    await setText(featureValueField(), 'updated_value')

    await createChangeRequest(
      'Update feature value',
      'Updating value from initial_value to updated_value',
    )

    log('Verify change request was created')
    await closeModal()

    log('Verify value has NOT changed yet (change request not approved)')
    await tryItExpect(featureName, 'value', 'initial_value')

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
    await visualSnapshot(page, 'change-requests-list', testInfo)

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
    await page.reload({ waitUntil: 'domcontentloaded' })
    await waitForElementVisible('#show-create-feature-btn')
    await gotoFeature(featureName)
    await expect(featureValueField()).toHaveText('updated_value', { timeout: 15000 })
    await closeModal()

    log('Verify value via API')
    await tryItExpect(featureName, 'value', 'updated_value')

    log('Verify change request is no longer in list')
    await gotoChangeRequests()
    await assertChangeRequestCount(0)

    log('Change request test completed successfully')
  })

  test('A segment override change request in a versioned environment opens on its Segment Overrides diff @enterprise', async ({
    page,
  }) => {
    const {
      addSegmentOverrideConfigForSegment,
      closeModal,
      createChangeRequest,
      createEnvironment,
      createRemoteConfig,
      createSegment,
      enableChangeRequests,
      enableFeatureVersioning,
      gotoChangeRequests,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      gotoSegments,
      login,
      openChangeRequest,
    } = createHelpers(page)
    const flagsmith = await getFlagsmith()
    if (
      !flagsmith.hasFeature('segment_change_requests') ||
      !flagsmith.hasFeature('feature_versioning')
    ) {
      log('Skipping versioned change request test, feature not enabled.')
      test.skip()
      return
    }

    const segmentName = 'cr_versioned_segment'
    const featureName = 'cr_versioned_feature'

    log('Login as admin')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Create a versioned environment that requires change requests')
    await page.click('text="Create Environment"')
    await createEnvironment('CR_Versioned_Env')
    await enableFeatureVersioning()
    await enableChangeRequests(1)

    log('Create the segment and feature')
    await gotoSegments()
    await createSegment(segmentName, [
      { name: 'plan', operator: 'EQUAL', value: 'pro' },
    ])
    await createRemoteConfig({ name: featureName, value: 'initial_value' })

    log('Create a change request that only overrides the segment')
    await gotoFeatures()
    await gotoFeature(featureName)
    await addSegmentOverrideConfigForSegment(segmentName, 'pro_value')
    await createChangeRequest('Override for pro plan', 'Segment override only', {
      openWith: '#update-feature-segments-btn',
    })
    await closeModal()

    log('The diff opens on Segment Overrides, the only tab with changes')
    await gotoChangeRequests()
    await openChangeRequest(0)
    await expect(
      page.getByRole('button', { name: /^Segment Overrides/ }),
    ).toHaveClass(/tab-active/)
  })

  test('An open change request can be edited from its page @enterprise', async ({
    page,
  }) => {
    const {
      closeModal,
      createChangeRequest,
      createEnvironment,
      createRemoteConfig,
      editChangeRequest,
      enableChangeRequests,
      featureValueField,
      gotoChangeRequests,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      login,
      openChangeRequest,
      setText,
      updateChangeRequest,
    } = createHelpers(page)
    const flagsmith = await getFlagsmith()
    if (!flagsmith.hasFeature('segment_change_requests')) {
      log('Skipping change request edit test, feature not enabled.')
      test.skip()
      return
    }

    const featureName = 'cr_edit_feature'

    log('Login as admin')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Create an environment that requires change requests')
    await page.click('text="Create Environment"')
    await createEnvironment('CR_Edit_Env')
    await enableChangeRequests(1)
    await createRemoteConfig({ name: featureName, value: 'initial_value' })

    log('Create a change request')
    await gotoFeatures()
    await gotoFeature(featureName)
    await setText(featureValueField(), 'first_value')
    await createChangeRequest('Change the value', 'First version')
    await closeModal()

    log('Edit it from its page')
    await gotoChangeRequests()
    await openChangeRequest(0)
    await editChangeRequest()
    await setText(featureValueField(), 'second_value')
    await updateChangeRequest()
    await expect(page.getByText(/Updated Change Request #\d+/)).toBeVisible()

    log('The change request now carries the edited value')
    await expect(page.getByText('second_value').first()).toBeVisible()
  })

  test('A change request scheduled for later shows as a scheduled change @enterprise', async ({
    page,
  }) => {
    const {
      closeModal,
      createChangeRequest,
      createEnvironment,
      createRemoteConfig,
      enableChangeRequests,
      featureValueField,
      gotoChangeRequests,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      login,
      openChangeRequest,
      setText,
    } = createHelpers(page)
    const flagsmith = await getFlagsmith()
    if (!flagsmith.hasFeature('segment_change_requests')) {
      log('Skipping scheduled change request test, feature not enabled.')
      test.skip()
      return
    }

    const featureName = 'cr_schedule_feature'

    log('Login as admin')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Create an environment that requires change requests')
    await page.click('text="Create Environment"')
    await createEnvironment('CR_Schedule_Env')
    await enableChangeRequests(1)
    await createRemoteConfig({ name: featureName, value: 'initial_value' })

    log('Create a change request scheduled for 2099')
    await gotoFeatures()
    await gotoFeature(featureName)
    await setText(featureValueField(), 'scheduled_value')
    await createChangeRequest('Scheduled value', 'Goes live in 2099', {
      scheduleFor: 'January 1, 2099 12:00 PM',
    })
    await closeModal()

    log('Its page shows it as a scheduled change')
    await gotoChangeRequests()
    await openChangeRequest(0)
    await expect(page.getByText('Scheduled Change')).toBeVisible()
    await expect(page.getByText(/1st Jan 2099/)).toBeVisible()
  })
})
