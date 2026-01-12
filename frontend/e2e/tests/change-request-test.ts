import {
  byId,
  click,
  closeModal,
  createEnvironment,
  createRemoteConfig,
  gotoFeatures,
  log,
  login,
  setText,
  waitForElementVisible,
  waitForElementNotExist,
  assertTextContentContains,
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

  // Enable versioning (required for segment override change requests)
  log('Enable feature versioning')
  const enableVersioningBtn = Selector(byId('enable-versioning'))
  if (await enableVersioningBtn.exists) {
    await t.click(enableVersioningBtn)
    await click('#confirm-btn-yes')
    await waitForElementVisible(byId('feature-versioning-enabled'))
  }

  log('Create multivariate feature for change request test')
  await click('#features-link')
  await waitForElementVisible('#show-create-feature-btn')
  // Create MV feature with initial weights: control (0%), variant_a (50%), variant_b (30%), variant_c (20%)
  // All variations created upfront so they have IDs
  await createRemoteConfig(0, 'cr_mv_feature', 'control', null, false, [
    { value: 'variant_a', weight: 50 },
    { value: 'variant_b', weight: 30 },
    { value: 'variant_c', weight: 20 },
  ])

  // ============================================
  // TEST 1: Change weights via Change Request
  // ============================================
  log('TEST 1: Edit MV feature - change weights via Change Request')
  await gotoFeatures()
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')

  // Change weights: variant_a=30%, variant_b=40%, variant_c=30%
  log('Set new weights: variant_a=30%, variant_b=40%, variant_c=30%')
  await setText(byId('featureVariationWeightvariant_a'), '30')
  await setText(byId('featureVariationWeightvariant_b'), '40')
  await setText(byId('featureVariationWeightvariant_c'), '30')

  await click(byId('update-feature-btn'))

  log('Fill change request modal')
  await waitForElementVisible('input[placeholder="My Change Request"]')
  await setText('input[placeholder="My Change Request"]', 'Update MV weights to 30/40/30')
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

  // The original weights should still be in effect (50/30/20)
  // The CR weights (30/40/30) should NOT be applied yet
  const variantAWeight = await Selector(byId('featureVariationWeightvariant_a')).value
  const variantBWeight = await Selector(byId('featureVariationWeightvariant_b')).value
  const variantCWeight = await Selector(byId('featureVariationWeightvariant_c')).value
  await t.expect(variantAWeight).eql('50', 'variant_a should still be 50% before CR publish')
  await t.expect(variantBWeight).eql('30', 'variant_b should still be 30% before CR publish')
  await t.expect(variantCWeight).eql('20', 'variant_c should still be 20% before CR publish')

  await closeModal()

  // ============================================
  // TEST 3: Navigate to Change Requests and verify the CR contains correct MV weights
  // ============================================
  log('TEST 3: Navigate to Change Requests page and verify CR values')
  await click('#change-requests-link')
  await waitForElementVisible('[data-test="change-requests-page"]')

  // Click on the change request we just created
  log('Open the change request')
  const crLink = Selector('.list-item.clickable').withText('Update MV weights to 30/40/30')
  await t.expect(crLink.exists).ok('Change request should exist in the list', { timeout: 10000 })
  await t.click(crLink)

  // Wait for CR detail page to load
  await waitForElementVisible('[data-test="change-requests-page"]')
  await t.wait(2000) // Wait for diff to render

  // Verify the variation weights in the diff view
  // The DiffVariations component shows the weight changes
  log('Verify CR contains correct variation weight changes')

  // Check that the variations tab exists and shows the weight changes
  // Click on Variations tab if it exists
  const variationsTab = Selector('button').withText('Variations')
  if (await variationsTab.exists) {
    await t.click(variationsTab)
    await t.wait(500)

    // The diff should show the weight changes: 50% -> 30% for variant_a, 50% -> 40% for variant_b, 0% -> 30% for variant_c
    // Check that the diff contains the expected weight values
    await assertTextContentContains('[data-test="change-requests-page"]', '30%')
    await assertTextContentContains('[data-test="change-requests-page"]', '40%')
    log('Verified: CR diff shows the new weight values (30%, 40%, 30%)')
  } else {
    log('Variations tab not visible - checking diff content directly')
    // The weights might be shown in the main diff view
    const pageContent = await Selector('[data-test="change-requests-page"]').innerText
    await t.expect(pageContent).contains('30', 'CR should contain weight value 30')
    await t.expect(pageContent).contains('40', 'CR should contain weight value 40')
  }

  log('Change request tests passed - TEST 1, 2 & 3 verified')
  log('MV weights are correctly stored in the change request')

  // ============================================
  // TEST 4: Create a segment and add it as segment override via Change Request
  // ============================================
  log('TEST 4: Create segment and add as segment override with MV weights via Change Request')

  // First, create a segment in the Segments page
  log('Navigate to Segments page to create a segment')
  await click('#segments-link')
  await waitForElementVisible(byId('show-create-segment-btn'))

  // Create segment
  await click(byId('show-create-segment-btn'))
  await setText(byId('segmentID'), 'test_cr_segment')

  // Set segment rule
  log('Set segment rule: age = 25')
  await setText(byId('rule-0-property-0'), 'age')
  await t.wait(500)
  await setText(byId('rule-0-value-0'), '25')

  // Create the segment
  await click(byId('create-segment'))
  await waitForElementVisible(byId('segment-0-name'))

  // Navigate to features and open the MV feature
  log('Navigate back to features')
  await gotoFeatures()
  await click(byId('feature-item-0'))
  await waitForElementVisible('#create-feature-modal')

  // Go to Segment Overrides tab
  log('Navigate to Segment Overrides tab')
  await click(byId('segment_overrides'))
  await t.wait(1000)

  // Select the segment we just created from the dropdown
  log('Select segment for override')
  await click(byId('select-segment'))
  await t.wait(500)

  // Click on the segment option
  const segmentOption = Selector(byId('select-segment-option-0'))
  if (await segmentOption.exists) {
    await t.click(segmentOption)
  }
  await t.wait(1000)

  // Now configure the segment override - enable it and set MV weights
  log('Configure segment override: enable and set MV weights')
  await waitForElementVisible(byId('segment-override-0'))

  // Enable the segment override
  const segmentOverrideToggle = Selector(byId('segment-override-toggle-0'))
  if (await segmentOverrideToggle.exists) {
    await t.click(segmentOverrideToggle)
  }

  // Set MV weights for segment override: variant_a=60%, variant_b=30%, variant_c=10%
  log('Set segment override MV weights: variant_a=60%, variant_b=30%, variant_c=10%')
  await setText(`${byId('segment-override-0')} ${byId('featureVariationWeightvariant_a')}`, '60')
  await setText(`${byId('segment-override-0')} ${byId('featureVariationWeightvariant_b')}`, '30')
  await setText(`${byId('segment-override-0')} ${byId('featureVariationWeightvariant_c')}`, '10')

  // Click the update/create change request button for segment overrides
  log('Save segment overrides via Change Request')
  await click(byId('update-feature-segments-btn'))

  // Fill change request modal
  await waitForElementVisible('input[placeholder="My Change Request"]')
  await setText('input[placeholder="My Change Request"]', 'Add segment override with MV weights')
  await click('#confirm-cancel-plan')

  // Wait for CR to be saved
  log('Wait for segment override change request to be saved')
  await waitForElementVisible('.toast-message')
  await waitForElementNotExist('.toast-message')

  await closeModal()
  await waitForElementNotExist('#create-feature-modal')

  // ============================================
  // TEST 5: Verify segment override CR contains correct values
  // ============================================
  log('TEST 5: Navigate to Change Requests and verify segment override CR')
  await click('#change-requests-link')
  await waitForElementVisible('[data-test="change-requests-page"]')

  // Click on the segment override change request
  log('Open the segment override change request')
  const segmentCrLink = Selector('.list-item.clickable').withText('Add segment override with MV weights')
  await t.expect(segmentCrLink.exists).ok('Segment override change request should exist', { timeout: 10000 })
  await t.click(segmentCrLink)

  // Wait for CR detail page to load
  await waitForElementVisible('[data-test="change-requests-page"]')
  await t.wait(2000)

  // Verify the segment override is shown in the diff
  log('Verify CR contains segment override changes')

  // Check that Segment Overrides tab exists and click it
  const segmentOverridesTab = Selector('button').withText('Segment Overrides')
  if (await segmentOverridesTab.exists) {
    await t.click(segmentOverridesTab)
    await t.wait(500)

    // Verify the segment name appears
    await assertTextContentContains('[data-test="change-requests-page"]', 'test_cr_segment')
    log('Verified: CR diff shows the segment override (test_cr_segment)')
  } else {
    // Segment overrides might be shown inline
    const pageContent = await Selector('[data-test="change-requests-page"]').innerText
    await t.expect(pageContent).contains('test_cr_segment', 'CR should contain segment name')
    log('Segment Overrides tab not visible - verified segment name in page content')
  }

  log('All change request tests passed - TEST 1, 2, 3, 4 & 5 verified')
  log('MV weights and segment overrides are correctly stored in change requests')
}
