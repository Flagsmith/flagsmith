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
  waitForElementNotExist,
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

  log('Enable change requests on environment')
  await click('[data-test="js-feature-change-requests"]')
  await waitForElementVisible('[name="env-name"]')

  log('Create multivariate feature for change request test')
  await click('#features-link')
  await waitForElementVisible('#show-create-feature-btn')
  // Create MV feature with initial weights: control (0%), variant_a (50%), variant_b (50%)
  await createRemoteConfig(0, 'cr_mv_feature', 'control', null, false, [
    { value: 'variant_a', weight: 50 },
    { value: 'variant_b', weight: 50 },
  ])

  // ============================================
  // TEST 1: Add new variation and change weights via Change Request
  // ============================================
  log('TEST 1: Edit MV feature - add new variation and change weights')
  await gotoFeatures()
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')

  // Add a new variation
  log('Add new variation: variant_c')
  await click(byId('add-variation'))
  await setText(byId('featureVariationValue2'), 'variant_c')

  // Change weights: variant_a=30%, variant_b=40%, variant_c=30%
  log('Set new weights: variant_a=30%, variant_b=40%, variant_c=30%')
  await setText(byId('featureVariationWeightvariant_a'), '30')
  await setText(byId('featureVariationWeightvariant_b'), '40')
  await setText(byId('featureVariationWeightvariant_c'), '30')

  await click(byId('update-feature-btn'))

  log('Fill change request modal')
  await waitForElementVisible('input[placeholder="My Change Request"]')
  await setText('input[placeholder="My Change Request"]', 'Add variant_c and update weights')
  await click('#confirm-cancel-plan')

  log('Wait for change request to be saved')
  await waitForElementVisible('.toast-message')
  await waitForElementNotExist('.toast-message')

  log('Close the feature modal')
  await closeModal()
  await waitForElementNotExist('#create-feature-modal')

  // ============================================
  // TEST 2: Verify values are NOT updated before CR is published
  // ============================================
  log('TEST 2: Verify feature values are NOT updated yet (CR not published)')
  await gotoFeatures()
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')

  // The original weights should still be in effect (50/50)
  // variant_c should NOT exist yet in the live feature
  const variantAWeight = await Selector(byId('featureVariationWeightvariant_a')).value
  const variantBWeight = await Selector(byId('featureVariationWeightvariant_b')).value
  await t.expect(variantAWeight).eql('50', 'variant_a should still be 50% before CR publish')
  await t.expect(variantBWeight).eql('50', 'variant_b should still be 50% before CR publish')

  // variant_c input should not exist (only 2 variations)
  const variantCExists = await Selector(byId('featureVariationWeightvariant_c')).exists
  await t.expect(variantCExists).eql(false, 'variant_c should not exist before CR publish')

  await closeModal()

  // ============================================
  // TEST 3: Navigate to CR page and verify pending weights
  // ============================================
  log('TEST 3: Navigate to Change Requests and verify pending weights')
  await waitForElementVisible('#change-requests-link')
  await click('#change-requests-link')
  await waitForElementVisible(byId('change-requests-page'))

  log('Wait for change request list to load')
  await waitForElementVisible('.list-item.clickable')

  log('Click on the change request')
  const crListItem = Selector('.list-item.clickable').nth(0)
  await t.click(crListItem)

  log('Wait for change request detail page to load')
  await waitForElementVisible(Selector('button').withText('Publish Change'))

  // Verify the CR shows the new weights (30/40/30)
  log('Verify CR shows new weights: 30%, 40%, 30%')
  // The CR detail page should show the proposed changes
  const crPageContent = await Selector('.change-request-detail, [data-test="change-request-detail"]').exists
  if (crPageContent) {
    // Check that the variation weights are visible in the CR
    const pageText = await Selector('body').innerText
    await t.expect(pageText).contains('30', 'CR should show 30% weight')
    await t.expect(pageText).contains('40', 'CR should show 40% weight')
  }

  // ============================================
  // TEST 4: Publish CR and verify values are updated
  // ============================================
  log('TEST 4: Publish the change request')
  await clickByText('Publish Change', 'button')

  log('Confirm publish')
  await waitForElementVisible(Selector('button').withText('OK'))
  await clickByText('OK', 'button')

  log('Wait for publish to complete')
  await waitForElementVisible('.toast-message')
  await waitForElementNotExist('.toast-message')

  // ============================================
  // TEST 5: Verify values ARE updated after CR publish
  // ============================================
  log('TEST 5: Verify feature values ARE updated after CR publish')
  await click('#features-link')
  await waitForElementVisible(byId('feature-item-0'))

  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')

  // Now the new weights should be in effect (30/40/30)
  const newVariantAWeight = await Selector(byId('featureVariationWeightvariant_a')).value
  const newVariantBWeight = await Selector(byId('featureVariationWeightvariant_b')).value
  const newVariantCWeight = await Selector(byId('featureVariationWeightvariant_c')).value

  await t.expect(newVariantAWeight).eql('30', 'variant_a should be 30% after CR publish')
  await t.expect(newVariantBWeight).eql('40', 'variant_b should be 40% after CR publish')
  await t.expect(newVariantCWeight).eql('30', 'variant_c should be 30% after CR publish')

  await closeModal()

  log('Change request test passed - all scenarios verified')
}
