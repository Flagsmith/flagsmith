import { test, expect } from '@playwright/test';
import {
  byId,
  click,
  closeModal,
  createFeature,
  createRemoteConfig,
  deleteFeature,
  editRemoteConfig,
  getText,
  log,
  login,
  toggleFeature,
  waitForElementVisible,
} from '../helpers/helpers';
import { E2E_USER, PASSWORD } from '../config';

test('@oss Feature flag management test', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-0');

  log('Create Features');
  await click(page, '#features-link');

  await createRemoteConfig(page, 0, 'header_size', 'big');
  await createRemoteConfig(page, 0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ]);
  await createFeature(page, 1, 'header_enabled', false);

  log('Create Short Life Feature');
  await createFeature(page, 3, 'short_life_feature', false);
  await page.evaluate(() => {
    window.scrollBy(0, 15000);
  });

  log('Delete Short Life Feature');
  await deleteFeature(page, 3, 'short_life_feature');
  await page.evaluate(() => {
    window.scrollBy(0, 30000);
  });

  log('Toggle Feature');
  await toggleFeature(page, 0, true);

  log('Try it');
  await page.waitForTimeout(2000);
  await click(page, '#try-it-btn');
  await page.waitForTimeout(1500);
  let text = await getText(page, '#try-it-results');
  let json;
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error('Try it results are not valid JSON');
  }
  expect(json.header_size.value).toBe('big');
  expect(json.mv_flag.value).toBe('big');
  expect(json.header_enabled.enabled).toBe(true);

  log('Update feature');
  await editRemoteConfig(page, 1, 12);

  log('Try it again');
  await page.waitForTimeout(2000);
  await click(page, '#try-it-btn');
  await page.waitForTimeout(1500);
  text = await getText(page, '#try-it-results');
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error('Try it results are not valid JSON');
  }
  expect(json.header_size.value).toBe(12);

  log('Change feature value to boolean');
  await editRemoteConfig(page, 1, false);

  log('Try it again 2');
  await page.waitForTimeout(2000);
  await click(page, '#try-it-btn');
  await page.waitForTimeout(1500);
  text = await getText(page, '#try-it-results');
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error('Try it results are not valid JSON');
  }
  expect(json.header_size.value).toBe(false);

  log('Switch environment');
  await click(page, byId('switch-environment-production'));

  log('Feature should be off under different environment');
  await waitForElementVisible(page, byId('switch-environment-production-active'));
  await waitForElementVisible(page, byId('feature-switch-0-off'));

  log('Clear down features');
  await deleteFeature(page, 1, 'header_size');
  await deleteFeature(page, 0, 'header_enabled');
});
