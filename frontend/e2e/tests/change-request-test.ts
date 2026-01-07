import {
  byId,
  click,
  clickByText,
  closeModal,
  createEnvironment,
  createRemoteConfig,
  gotoFeatures,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.cafe'
import { t, Selector } from 'testcafe'
import { E2E_USER, PASSWORD } from '../config'

export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-0')

  log('Go to features first')
  await waitForElementVisible('#features-link')
  await click('#features-link')

  // Test: Feature Change Request with multivariate feature in isolated environment
  log('Create new environment for feature change request test')
  await click('#create-env-link')
  await createEnvironment('CR Test Env')

  log('Navigate to environment settings')
  await waitForElementVisible('#features-link')
  await t.wait(1000) // Wait for sidebar to fully render
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
