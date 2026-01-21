import { test, expect } from '../test-setup';
import {
  byId,
  click,
  closeModal,
  createFeature,
  createRemoteConfig,
  deleteFeature,
  editRemoteConfig,
  log,
  login,
  parseTryItResults,
  scrollBy,
  toggleFeature,
  waitForElementVisible,
  waitForNetworkIdle,
  createHelpers,
} from '../helpers.playwright';
import { E2E_USER, PASSWORD } from '../config';

test.describe('Flag Tests', () => {
  test('test description @oss', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-0')

  log('Create Features')
  await helpers.click('#features-link')

  await createFeature(page, 0, 'header_enabled', false)
  await createRemoteConfig(page, 1, 'header_size', 'big')
  await createRemoteConfig(page, 2, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])

  log('Create Short Life Feature')
  await createFeature(page, 3, 'short_life_feature', false)
  await scrollBy(page, 0, 15000)

  log('Delete Short Life Feature')
  await deleteFeature(page, 3, 'short_life_feature')
  await scrollBy(page, 0, 30000)

  log('Toggle Feature')
  await toggleFeature(page, 0, true)

  log('Try it')
  await page.waitForTimeout(2000)
  await helpers.click('#try-it-btn')
  await page.waitForTimeout(500)
  let json = await parseTryItResults(page)
  await expect(json.header_size.value).toBe('big')
  await expect(json.mv_flag.value).toBe('big')
  await expect(json.header_enabled.enabled).toBe(true)

  log('Update feature')
  await editRemoteConfig(page, 1,12)

  log('Try it again')
  await page.waitForTimeout(5000)
  await helpers.click('#try-it-btn')
  await page.waitForTimeout(2000)
  json = await parseTryItResults(page)
  await expect(json.header_size.value).toBe(12)

  log('Change feature value to boolean')
  await editRemoteConfig(page, 1,false)

  log('Try it again 2')
  await page.waitForTimeout(5000)
  await helpers.click('#try-it-btn')
  await page.waitForTimeout(2000)
  json = await parseTryItResults(page)
  await expect(json.header_size.value).toBe(false)

  log('Switch environment')
  // Navigate back to features list so environment switcher is visible in navbar
  await helpers.gotoFeatures()
  await waitForNetworkIdle(page)
  await waitForElementVisible(page, byId('switch-environment-production'))
  await page.waitForTimeout(500)
  await helpers.click(byId('switch-environment-production'))

  log('Feature should be off under different environment')
  await helpers.waitForElementVisible(byId('switch-environment-production-active'))
  await helpers.waitForElementVisible(byId('feature-switch-0-off'))

  log('Clear down features')
  await deleteFeature(page, 1, 'header_size')
  await deleteFeature(page, 0, 'header_enabled')
  });
});
