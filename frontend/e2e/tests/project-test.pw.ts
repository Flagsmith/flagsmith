import { test, expect } from '@playwright/test';
import {
  assertInputValue,
  assertTextContent,
  byId,
  click,
  getFlagsmith,
  log,
  login,
  setText,
  waitForElementNotExist,
  waitForElementVisible,
  createHelpers,
} from '../helpers.playwright';
import { E2E_USER, PASSWORD } from '../config'

test.describe('Project Tests', () => {
  test('test description @oss', async ({ page }) => {
    const helpers = createHelpers(page);
  const flagsmith = await getFlagsmith()
  const hasSegmentChangeRequests = flagsmith.hasFeature('segment_change_requests')

  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-0')
  log('Edit Project')
  await helpers.click('#project-link')
  await helpers.click('#project-settings-link')
  await helpers.setText("[name='proj-name']", 'Test Project')
  await helpers.click('#save-proj-btn')
  await assertTextContent(page, `#project-link`, 'Test Project')

  if (hasSegmentChangeRequests) {
    log('Test Change Requests Approvals Setting')

    log('Test 1: Enable change requests (auto-save on toggle)')
    await helpers.click('[data-test="js-change-request-approvals"]')
    await helpers.waitForElementVisible('[name="env-name"]')
    log('Verify auto-save persisted after navigation')
    await helpers.click('#features-link')
    await helpers.click('#project-settings-link')
    await helpers.waitForElementVisible('[name="env-name"]')

    log('Test 2: Change minimum approvals to 3 (manual save)')
    await helpers.setText('[name="env-name"]', '3')
    await helpers.click('#save-env-btn')
    log('Verify value 3 persisted after navigation')
    await helpers.click('#features-link')
    await helpers.click('#project-settings-link')
    await helpers.waitForElementVisible('[name="env-name"]')
    await assertInputValue(page, '[name="env-name"]', '3')

    log('Test 3: Disable change requests (auto-save on toggle)')
    await helpers.click('[data-test="js-change-request-approvals"]')
    log('Verify disabled state persisted after navigation')
    await helpers.click('#features-link')
    await helpers.click('#project-settings-link')
    await helpers.waitForElementNotExist('[name="env-name"]')

    log('Test 4: Re-enable and change to 5 (manual save)')
    await helpers.click('[data-test="js-change-request-approvals"]')
    await helpers.waitForElementVisible('[name="env-name"]')
    await helpers.setText('[name="env-name"]', '5')
    await helpers.click('#save-env-btn')
    log('Verify value 5 persisted after navigation')
    await helpers.click('#features-link')
    await helpers.click('#project-settings-link')
    await helpers.waitForElementVisible('[name="env-name"]')
    await assertInputValue(page, '[name="env-name"]', '5')
  }

  });
});