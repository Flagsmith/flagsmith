import { test } from '../test-setup'
import { byId, log, createHelpers, visualSnapshot } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'

test.describe('SCIM Tests', () => {
  test('SCIM configuration can be created, regenerated, and deleted @enterprise', async ({ page }, testInfo) => {
    const {
      click,
      login,
      waitForElementVisible,
    } = createHelpers(page)

    log('Login')
    await login(E2E_USER, PASSWORD)

    log('Navigate to SSO tab in Organisation Settings')
    await waitForElementVisible(byId('organisation-link'))
    await click(byId('organisation-link'))
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))
    await click(byId('sso'))

    log('Ensure clean state')
    const createBtn = page.locator(byId('scim-create'))
    const deleteBtn = page.locator(byId('scim-delete'))
    await createBtn.or(deleteBtn).waitFor({ state: 'visible' })
    if (await deleteBtn.isVisible()) {
      await click(byId('scim-delete'))
      await click('#confirm-btn-yes')
      await waitForElementVisible(byId('scim-create'))
    }
    await visualSnapshot(page, 'scim-empty', testInfo)

    log('Create SCIM configuration')
    await click(byId('scim-create'))

    log('Token modal shows the bearer token')
    await waitForElementVisible(byId('scim-token-value'))
    await visualSnapshot(page, 'scim-token-modal', testInfo)

    log('Close token modal via inline confirmation')
    await click(byId('scim-token-done'))
    await click(byId('scim-token-confirm-done'))

    log('Configured state shows base URL')
    await waitForElementVisible(byId('scim-base-url'))
    await visualSnapshot(page, 'scim-configured', testInfo)

    log('Regenerate token')
    await click(byId('scim-regenerate'))
    await click('#confirm-btn-yes')
    await waitForElementVisible(byId('scim-token-value'))
    await click(byId('scim-token-done'))
    await click(byId('scim-token-confirm-done'))
    await waitForElementVisible(byId('scim-base-url'))

    log('Delete SCIM configuration')
    await click(byId('scim-delete'))
    await click('#confirm-btn-yes')

    log('Back to empty state')
    await waitForElementVisible(byId('scim-create'))
  })
})
