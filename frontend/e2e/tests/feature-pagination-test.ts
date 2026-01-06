import { t } from 'testcafe'

import {
  assertTextContentContains,
  byId,
  click,
  clearFeatureSearch,
  closeModal,
  getText,
  goToNextPage,
  goToPrevPage,
  gotoFeature,
  gotoFeatures,
  log,
  login,
  searchFeatures,
  setText,
  waitForElementNotExist,
  waitForElementVisible,
} from '../helpers.cafe'
import { E2E_USER, PASSWORD } from '../config'

/**
 * Test: Page 2 Features List
 *
 * Tests that navigating to page 2 of the features list works correctly.
 * Uses seed data: 55 `pagination_feature_XXX` features pre-created.
 */
export const page2FeaturesTest = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)

  // Use first project (has 55+ features from seed data)
  await click('#project-select-0')
  await gotoFeatures()

  // Verify we're on page 1 with pagination features
  log('Verify page 1')
  await waitForElementVisible(byId('feature-item-0'))

  // Navigate to page 2
  log('Navigate to page 2')
  await goToNextPage()

  // Verify page 2 shows features
  log('Verify page 2 features')
  await waitForElementVisible(byId('feature-item-0')) // First item on page 2

  // Open a feature on page 2 and verify it works
  log('Open feature on page 2')
  await gotoFeature(0)
  await waitForElementVisible('#create-feature-modal')
  await closeModal()

  // Navigate back to page 1
  log('Navigate back to page 1')
  await goToPrevPage()
  await waitForElementVisible(byId('feature-item-0'))

  log('Page 2 features test passed')
}

/**
 * Test: Search on Page 2
 *
 * Tests that searching for features while on page 2 works correctly.
 * Uses seed data: 55 `pagination_feature_XXX` features pre-created.
 */
export const searchOnPage2Test = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)

  // Use first project
  await click('#project-select-0')
  await gotoFeatures()

  // Navigate to page 2
  log('Navigate to page 2')
  await goToNextPage()

  // Search for a specific feature
  log('Search for feature')
  await searchFeatures('pagination_feature_052')

  // Verify search results - should show filtered results
  log('Verify search results')
  await waitForElementVisible(byId('feature-item-0'))

  // Verify the feature name matches search
  const featureRow = await getText(byId('feature-item-0'))
  await t.expect(featureRow).contains('pagination_feature_052')

  // Clear search
  log('Clear search')
  await clearFeatureSearch()

  // Verify features are shown again
  await waitForElementVisible(byId('feature-item-0'))

  log('Search on page 2 test passed')
}

/**
 * Test: Multivariate Change Request
 *
 * Tests that creating a change request for a feature with multivariate options
 * works correctly (no 400 error).
 * Uses seed data: `mv_test_feature` with multivariate options pre-created.
 */
export const multivariateChangeRequestTest = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)

  // Use first project (has mv_test_feature from seed data)
  await click('#project-select-0')

  // Enable change requests for this environment
  log('Enable change requests')
  await click('#project-settings-link')
  await click('[data-test="js-change-request-approvals"]')
  await waitForElementVisible('[name="env-name"]')
  await gotoFeatures()

  // Find and open the multivariate feature (created by seed data)
  log('Open multivariate feature')
  await searchFeatures('mv_test_feature')
  await waitForElementVisible(byId('feature-item-0'))
  await gotoFeature(0)

  // Modify multivariate weights
  log('Modify multivariate weights')
  await setText(byId('featureVariationWeightvariant_a'), '30')
  await setText(byId('featureVariationWeightvariant_b'), '70')

  // Create change request instead of saving directly
  log('Create change request')
  await click(byId('btn-schedule-change'))
  await waitForElementVisible('[name="title"]')
  await setText('[name="title"]', 'Update MV weights')
  await click('#create-change-request-btn')

  // Verify change request was created (no 400 error)
  await waitForElementVisible('.toast-message')
  await waitForElementNotExist('.toast-message')

  log('Multivariate change request test passed')
}
