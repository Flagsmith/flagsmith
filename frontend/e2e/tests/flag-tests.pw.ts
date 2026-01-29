import { test, expect } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import { E2E_USER, PASSWORD } from '../config';

test.describe('Flag Tests', () => {
  test('test description @oss', async ({ page }) => {
    const {
      click,
      createFeature,
      createRemoteConfig,
      deleteFeature,
      editRemoteConfig,
      gotoFeatures,
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
    await click('#project-select-0')

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
});
