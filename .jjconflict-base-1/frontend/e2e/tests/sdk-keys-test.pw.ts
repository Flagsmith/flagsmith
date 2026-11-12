import { test, expect } from '../test-setup'
import { byId, log, createHelpers } from '../helpers'
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config'

test.describe('SDK Keys Tests', () => {
  test('Server-side SDK keys can be created and deleted @oss', async ({
    page,
  }) => {
    const {
      click,
      gotoProject,
      login,
      setText,
      waitForElementVisible,
    } = createHelpers(page)

    log('Login')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Navigate to SDK Keys')
    await click('#sdk-keys-link')
    await waitForElementVisible('#server-side-keys-list, button:has-text("Create Server-side Environment Key")')

    log('Create server-side key')
    await page.locator('button').filter({ hasText: 'Create Server-side Environment Key' }).click()
    await waitForElementVisible('.modal-body')
    await setText('[name="name"]', 'Test E2E Key')
    await page.getByRole('button', { name: 'Create', exact: true }).click()

    log('Verify key appears in list')
    await page.waitForSelector('#server-side-keys-list')
    const keyRow = page.locator('.list-item').filter({ hasText: 'Test E2E Key' })
    await keyRow.waitFor({ state: 'visible', timeout: 10000 })

    log('Delete server-side key')
    await keyRow.locator('#remove-sdk-key').click()
    await waitForElementVisible('#confirm-btn-yes')
    await click('#confirm-btn-yes')

    log('Verify key is removed')
    await expect(keyRow).toHaveCount(0, { timeout: 10000 })
  })
})
