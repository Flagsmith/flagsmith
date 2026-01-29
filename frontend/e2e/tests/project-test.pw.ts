import { test, expect } from '../test-setup';
import { byId, getFlagsmith, log, createHelpers } from '../helpers.playwright';
import { E2E_USER, PASSWORD } from '../config'

test.describe('Project Tests', () => {
  test('test description @oss', async ({ page }) => {
    const {
      assertInputValue,
      assertTextContent,
      click,
      login,
      setText,
      waitForElementNotExist,
      waitForElementVisible,
    } = createHelpers(page);
    const flagsmith = await getFlagsmith()
    const hasSegmentChangeRequests = flagsmith.hasFeature('segment_change_requests')

    log('Login')
    await login(E2E_USER, PASSWORD)
    await click('#project-select-0')
    log('Edit Project')
    await click('#project-link')
    await click('#project-settings-link')
    await setText("[name='proj-name']", 'Test Project')
    await click('#save-proj-btn')
    await assertTextContent(`#project-link`, 'Test Project')

    if (hasSegmentChangeRequests) {
      log('Test Change Requests Approvals Setting')

      log('Test 1: Enable change requests (auto-save on toggle)')
      await click('[data-test="js-change-request-approvals"]')
      await waitForElementVisible('[name="env-name"]')
      log('Verify auto-save persisted after navigation')
      await click('#features-link')
      await click('#project-settings-link')
      await waitForElementVisible('[name="env-name"]')

      log('Test 2: Change minimum approvals to 3 (manual save)')
      await setText('[name="env-name"]', '3')
      await click('#save-env-btn')
      // Wait for save to complete
      await page.waitForTimeout(1000)
      log('Verify value 3 persisted after navigation')
      await click('#features-link')
      await click('#project-settings-link')
      await waitForElementVisible('[name="env-name"]')
      await assertInputValue('[name="env-name"]', '3')

      log('Test 3: Disable change requests (auto-save on toggle)')
      await click('[data-test="js-change-request-approvals"]')
      log('Verify disabled state persisted after navigation')
      await click('#features-link')
      await click('#project-settings-link')
      await waitForElementNotExist('[name="env-name"]')

      log('Test 4: Re-enable and change to 5 (manual save)')
      await click('[data-test="js-change-request-approvals"]')
      await waitForElementVisible('[name="env-name"]')
      await setText('[name="env-name"]', '5')
      await click('#save-env-btn')
      log('Verify value 5 persisted after navigation')
      await click('#features-link')
      await click('#project-settings-link')
      await waitForElementVisible('[name="env-name"]')
      await assertInputValue('[name="env-name"]', '5')
    }
  });
});