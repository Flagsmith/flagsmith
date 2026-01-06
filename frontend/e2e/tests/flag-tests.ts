import {
  byId,
  click,
  clickByText,
  closeModal,
  createEnvironment,
  createFeature,
  createRemoteConfig,
  deleteFeature,
  editRemoteConfig,
  gotoFeatures,
  log,
  login,
  parseTryItResults,
  setText,
  toggleFeature,
  waitForElementVisible,
} from '../helpers.cafe'
import { t, Selector } from 'testcafe'
import { E2E_USER, PASSWORD } from '../config'

export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-0')

  log('Go to features')
  await waitForElementVisible('#features-link')
  await click('#features-link')

  await createRemoteConfig(0, 'header_size', 'big')
  await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])
  await createFeature(1, 'header_enabled', false)

  log('Create Short Life Feature')
  await createFeature(3, 'short_life_feature', false)
  await t.eval(() => {
    window.scrollBy(0, 15000)
  })

  log('Delete Short Life Feature')
  await deleteFeature(3, 'short_life_feature')
  await t.eval(() => {
    window.scrollBy(0, 30000)
  })

  log('Toggle Feature')
  await toggleFeature(0, true)

  log('Try it')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(500)
  let json = await parseTryItResults()
  await t.expect(json.header_size.value).eql('big')
  await t.expect(json.mv_flag.value).eql('big')
  await t.expect(json.header_enabled.enabled).eql(true)

  log('Update feature')
  await editRemoteConfig(1, 12)

  log('Try it again')
  await t.wait(500)
  await click('#try-it-btn')
  await t.wait(500)
  json = await parseTryItResults()
  await t.expect(json.header_size.value).eql(12)

  log('Change feature value to boolean')
  await editRemoteConfig(1, false)

  log('Try it again 2')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(500)
  json = await parseTryItResults()
  await t.expect(json.header_size.value).eql(false)

  log('Switch environment')
  await click(byId('switch-environment-production'))

  log('Feature should be off under different environment')
  await waitForElementVisible(byId('switch-environment-production-active'))
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Switch back to Development environment')
  await click(byId('switch-environment-development'))
  await waitForElementVisible(byId('switch-environment-development-active'))

  log('Clear down features')
  await deleteFeature(1, 'header_size')
  await deleteFeature(0, 'header_enabled')
  await deleteFeature(0, 'mv_flag')

  log('Create multivariate feature for toggle test')
  await createRemoteConfig(
    0,
    'mv_toggle_test',
    'control',
    'MV toggle test',
    false,
    [
      { value: 'variant_a', weight: 50 },
      { value: 'variant_b', weight: 50 },
    ],
  )

  log('Toggle multivariate feature via edit modal')
  await gotoFeatures()
  await click(byId('feature-switch-0-on'))
  await waitForElementVisible('#create-feature-modal')
  await click(byId('toggle-feature-button'))
  await click(byId('update-feature-btn'))
  await closeModal()
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Multivariate toggle test passed')
  await deleteFeature(0, 'mv_toggle_test')

  // Test: Feature Change Request with multivariate feature in isolated environment
  log('Create new environment for feature change request test')
  await click('#create-env-link')
  await createEnvironment('CR Test Env')

  log('Enable feature change requests in environment settings')
  await waitForElementVisible('#env-settings-link')
  await click('#env-settings-link')

  // Check if 4_EYES feature is available (plan-based)
  const hasFeatureChangeRequests = await Selector(
    '[data-test="js-feature-change-requests"]',
  ).exists
  if (!hasFeatureChangeRequests) {
    log('Skipping change request test - 4_EYES feature not available')
    await click('#features-link')
    return
  }

  await click('[data-test="js-feature-change-requests"]')
  await waitForElementVisible('[name="env-name"]')

  log('Create multivariate feature for change request test')
  await click('#features-link')
  await createRemoteConfig(0, 'cr_mv_feature', 'control', null, false, [
    { value: 'variant_a', weight: 50 },
    { value: 'variant_b', weight: 50 },
  ])

  log('Edit multivariate feature to create change request')
  await gotoFeatures()
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')
  await setText(byId('featureValue'), 'updated_value')
  await click(byId('update-feature-btn'))

  log('Fill change request modal')
  await waitForElementVisible('input[placeholder="My Change Request"]')
  await setText('input[placeholder="My Change Request"]', 'Test CR')
  await click('#confirm-cancel-plan')
  await t.wait(1000) // Wait for CR to be saved before navigating

  log('Close the feature modal')
  await closeModal()

  log('Navigate to change requests')
  await waitForElementVisible(byId('feature-item-0'))
  await click('#change-requests-link')
  await waitForElementVisible(byId('change-requests-page'))

  log('Wait for change request list to load')
  await t.wait(2000)

  log('Click on the change request')
  // Click on the first list item which should be our change request
  await waitForElementVisible('.list-item.clickable')
  await t.click(Selector('.list-item.clickable').nth(0))

  log('Wait for change request detail page to load')
  await t.wait(2000)

  log('Publish the change request')
  await clickByText('Publish Change', 'button')
  await t.wait(500)
  await clickByText('OK', 'button')

  log('Verify change was published - go back to features')
  await t.wait(1000)
  await click('#features-link')
  await waitForElementVisible(byId('feature-item-0'))

  log('Verify the updated value')
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')
  const featureValue = await Selector(byId('featureValue')).value
  await t.expect(featureValue).eql('updated_value')
  await closeModal()

  log('Change request test passed')
}
