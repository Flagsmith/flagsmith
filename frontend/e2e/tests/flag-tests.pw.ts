import { test, expect } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config';

test.describe('Flag Tests', () => {
  test('Feature flags can be created, toggled, edited, and deleted across environments @oss', async ({ page }) => {
    const {
      click,
      createFeature,
      createRemoteConfig,
      deleteFeature,
      editRemoteConfig,
      gotoFeatures,
      gotoProject,
      login,
      parseTryItResults,
      scrollBy,
      toggleFeature,
      waitForElementClickable,
      waitForElementVisible,
      waitForFeatureSwitch,
    } = createHelpers(page);

    log('Login')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    // Check if we're already in production by checking if development is clickable
    const isProductionActive = await page.locator(byId('switch-environment-development')).isVisible().catch(() => true)

    if (isProductionActive) {
      // We're not in development (might be in production), switch to development first
      log('Switching to development first')
      await waitForElementClickable(byId('switch-environment-development'))
      await click(byId('switch-environment-development'))
      await page.waitForTimeout(500)
    }

    log('Create Features')
    await click('#features-link')

    await createFeature({ name: 'header_enabled', value: false })
    await createRemoteConfig({ name: 'header_size', value: 'big' })
    await createRemoteConfig({ name: 'mv_flag', value: 'big', mvs: [
      { value: 'medium', weight: 100 },
      { value: 'small', weight: 0 },
    ]})

    log('Create Short Life Feature')
    await createFeature({ name: 'short_life_feature', value: false })
    await scrollBy(0, 15000)

    log('Delete Short Life Feature')
    await deleteFeature('short_life_feature')
    await scrollBy(0, 30000)

    log('Toggle Feature')
    await toggleFeature('header_enabled', true)

    log('Try it')
    await page.waitForTimeout(2000)
    await click('#try-it-btn')
    await page.waitForTimeout(500)
    let json = await parseTryItResults()
    await expect(json.header_size.value).toBe('big')
    await expect(json.mv_flag.value).toBe('big')
    await expect(json.header_enabled.enabled).toBe(true)

    log('Update feature')
    await editRemoteConfig('header_size', 12)

    log('Try it again')
    await page.waitForTimeout(5000)
    await click('#try-it-btn')
    await page.waitForTimeout(2000)
    json = await parseTryItResults()
    await expect(json.header_size.value).toBe(12)

    log('Change feature value to boolean')
    await editRemoteConfig('header_size', false)

    log('Try it again 2')
    await page.waitForTimeout(5000)
    await click('#try-it-btn')
    await page.waitForTimeout(2000)
    json = await parseTryItResults()
    await expect(json.header_size.value).toBe(false)

    log('Switch environment')
    // Navigate back to features list so environment switcher is visible in navbar
    await gotoFeatures()
    // Wait for page to be fully loaded and features page to be ready
    await page.waitForLoadState('load')
    await waitForElementVisible('#show-create-feature-btn')

    // Wait a moment for environment switcher to render
    await page.waitForTimeout(500)

    // Now we're definitely in development, switch to production
    log('Switching to production')
    await waitForElementClickable(byId('switch-environment-production'))
    await click(byId('switch-environment-production'))

    log('Feature should be off under different environment')
    await waitForElementVisible(byId('switch-environment-production-active'))
    await waitForFeatureSwitch('header_enabled', 'off')

    log('Clear down features')
    // Ensure features list is fully loaded before attempting to delete
    await waitForFeatureSwitch('header_enabled', 'off')
    await deleteFeature('header_size')
    await deleteFeature('header_enabled')
  });

  test('Feature flags can have tags added and be archived @oss', async ({ page }) => {
    const {
      addTagToFeature,
      archiveFeature,
      click,
      clickByText,
      closeModal,
      createFeature,
      createTag,
      deleteFeature,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      login,
      waitForToast,
    } = createHelpers(page);

    log('Login')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Create Tags')
    // Navigate to features first to ensure we're in the right context
    await gotoFeatures()

    // Create first tag
    await createTag('bug', '#FF6B6B')

    // Create second tag
    await createTag('feature-request', '#4ECDC4')

    log('Create Feature with Settings')
    await createFeature({ name: 'test_flag_with_tags', value: true, description: 'Test flag for tag and archive operations' })

    log('Create additional feature to keep filters visible')
    await createFeature({ name: 'keep_filters_visible', value: false })

    log('Open Feature and Add Tags')
    await gotoFeature('test_flag_with_tags')
    await addTagToFeature('bug')
    await addTagToFeature('feature-request')

    // Save the feature settings
    await clickByText('Update Settings');
    await closeModal()

    log('Archive Feature')
    await gotoFeature('test_flag_with_tags')
    await archiveFeature()
    await waitForToast()

    log('Verify Archive')
    await closeModal()

    // Verify the feature can be filtered as archived
    await gotoFeatures()

    // Verify archived feature is not visible by default
    const archivedFeatureHidden = await page.locator('[data-test^="feature-item-"]').filter({
      has: page.locator(`span:text-is("test_flag_with_tags")`)
    }).count()
    expect(archivedFeatureHidden).toBe(0)

    log('Enable archived filter')
    // Click on Tags filter button
    await click(byId('table-filter-tags'))

    // Click on archived filter option
    await clickByText(/^archived/, '.table-filter-item')

    // Close the filter dropdown
    await click(byId('table-filter-tags'))

    log('Verify archived feature is now visible')
    // Wait for the features list to update and verify archived feature appears
    const archivedFeature = page.locator('[data-test^="feature-item-"]').filter({
      has: page.locator(`span:text-is("test_flag_with_tags")`)
    }).first()
    await archivedFeature.waitFor({ state: 'visible', timeout: 5000 })

  });
});
