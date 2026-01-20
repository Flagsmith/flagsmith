import { test, expect } from '@playwright/test';
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
  toggleFeature,
  waitForElementVisible,
} from '../helpers.pw';
import { t } from 'testcafe';
import { E2E_USER, PASSWORD } from '../config';

test.describe('TestName', () => {
  test('test description', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-0')

  log('Create Features')
  await helpers.click('#features-link')

  await createRemoteConfig(0, 'header_size', 'big')
  await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])
  await createFeature(1, 'header_enabled', false)

  log('Create Short Life Feature')
  await createFeature(3, 'short_life_feature', false)
  await eval(() => {
    window.scrollBy(0, 15000)
  })

  log('Delete Short Life Feature')
  await deleteFeature(3, 'short_life_feature')
  await eval(() => {
    window.scrollBy(0, 30000)
  })

  log('Toggle Feature')
  await toggleFeature(0, true)

  log('Try it')
  await wait(2000)
  await helpers.click('#try-it-btn')
  await wait(500)
  let json = await parseTryItResults()
  await expect(json.header_size.value).toBe('big')
  await expect(json.mv_flag.value).toBe('big')
  await expect(json.header_enabled.enabled).toBe(true)

  log('Update feature')
  await editRemoteConfig(1,12)

  log('Try it again')
  await wait(500)
  await helpers.click('#try-it-btn')
  await wait(500)
  json = await parseTryItResults()
  await expect(json.header_size.value).toBe(12)

  log('Change feature value to boolean')
  await editRemoteConfig(1,false)

  log('Try it again 2')
  await wait(500)
  await helpers.click('#try-it-btn')
  await wait(500)
  json = await parseTryItResults()
  await expect(json.header_size.value).toBe(false)

  log('Switch environment')
  await helpers.click(byId('switch-environment-production'))

  log('Feature should be off under different environment')
  await helpers.waitForElementVisible(byId('switch-environment-production-active'))
  await helpers.waitForElementVisible(byId('feature-switch-0-off'))

  log('Clear down features')
  await deleteFeature(1, 'header_size')
  await deleteFeature(0, 'header_enabled')
  });
});