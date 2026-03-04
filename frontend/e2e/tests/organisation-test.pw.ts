import { test, expect } from '../test-setup';
import { byId, log, createHelpers, LONG_TIMEOUT } from '../helpers'
import { E2E_SEPARATE_TEST_USER, PASSWORD } from '../config'

test.describe('Organisation Tests', () => {
  test('Organisations can be created, renamed, and deleted with name validation @oss', async ({ page }) => {
    const {
      assertTextContent,
      click,
      clickByText,
      closeModal,
      getInputValue,
      login,
      setText,
      waitForElementNotExist,
      waitForElementVisible,
      waitForModalToClose,
    } = createHelpers(page);

    log('Login')
    await login(E2E_SEPARATE_TEST_USER, PASSWORD)

    log('Navigate to Organisation Settings')
    await waitForElementVisible(byId('organisation-link'))
    await click(byId('organisation-link'))
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))

    log('Edit Organisation Name')
    await waitForElementVisible("[data-test='organisation-name']")
    await setText("[data-test='organisation-name']", 'Test Organisation')
    await click('#save-org-btn')

    log('Verify Organisation Name Updated in Breadcrumb')
    await click('#projects-link')
    await assertTextContent('#organisation-link', 'Test Organisation')

    log('Verify Organisation Name Persisted in Settings')
    await click(byId('organisation-link'))
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))
    await waitForElementVisible("[data-test='organisation-name']")

    log('Test 2: Create and Delete Organisation, Verify Next Org in Nav')
    log('Navigate to create organisation')
    await click(byId('home-link'))
    await waitForElementVisible(byId('create-organisation-btn'))
    await click(byId('create-organisation-btn'))

    log('Create New Organisation')
    await waitForElementVisible("[name='orgName']")
    await setText("[name='orgName']", 'E2E Test Org to Delete')
    await click('#create-org-btn')
    await waitForModalToClose()

    log('Verify New Organisation Created and appears in nav')
    await waitForElementVisible(byId('organisation-link'))
    await assertTextContent('#organisation-link', 'E2E Test Org to Delete')

    log('Navigate back to the org we want to delete')
    const deleteOrgUrl = page.url()
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))

    log('Delete Organisation')
    await waitForElementVisible('#delete-org-btn')
    await click('#delete-org-btn')
    await waitForElementVisible("[name='confirm-org-name']")
    await setText("[name='confirm-org-name']", 'E2E Test Org to Delete')
    await clickByText('Confirm')

    log('Verify Redirected away from deleted Organisation')
    await page.waitForURL((url) => url.href !== deleteOrgUrl, { timeout: LONG_TIMEOUT })
    await waitForElementVisible(byId('organisation-link'))
    await expect(page.locator('#organisation-link')).not.toContainText('E2E Test Org to Delete')

    log('Test 3: Cancel Organisation Deletion')
    log('Create temporary organisation for cancel test')
    await click(byId('home-link'))
    await waitForElementVisible(byId('create-organisation-btn'))
    await click(byId('create-organisation-btn'))
    await waitForElementVisible("[name='orgName']")
    await setText("[name='orgName']", 'E2E Cancel Test Org')
    await click('#create-org-btn')
    await waitForModalToClose()

    log('Navigate to org settings and open delete modal')
    await waitForElementVisible(byId('organisation-link'))
    await assertTextContent('#organisation-link', 'E2E Cancel Test Org')
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))
    await waitForElementVisible('#delete-org-btn')
    await click('#delete-org-btn')
    await waitForElementVisible("[name='confirm-org-name']")
    await setText("[name='confirm-org-name']", 'E2E Cancel Test Org')

    log('Close modal without confirming deletion')
    await closeModal()
    await waitForElementNotExist('.modal')

    log('Verify organisation still exists in navbar')
    await waitForElementVisible(byId('organisation-link'))
    await assertTextContent('#organisation-link', 'E2E Cancel Test Org')

    log('Clean up: Delete the test organisation')
    const cancelTestOrgUrl = page.url()
    await click('#delete-org-btn')
    await waitForElementVisible("[name='confirm-org-name']")
    await setText("[name='confirm-org-name']", 'E2E Cancel Test Org')
    await clickByText('Confirm')
    await page.waitForURL((url) => url.href !== cancelTestOrgUrl, { timeout: LONG_TIMEOUT })
    await waitForElementVisible(byId('organisation-link'))
    await expect(page.locator('#organisation-link')).not.toContainText('E2E Cancel Test Org')

    log('Test 4: Organisation Name Validation')
    log('Navigate to Test Organisation settings')
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))

    log('Test empty organisation name validation')
    await waitForElementVisible("[data-test='organisation-name']")
    const originalName = await getInputValue("[data-test='organisation-name']")

    log('Clear organisation name')
    await setText("[data-test='organisation-name']", '')

    log('Verify save button is disabled')
    const saveButton = page.locator('#save-org-btn')
    await expect(saveButton).toBeDisabled()

    log('Restore original name')
    await setText("[data-test='organisation-name']", originalName)

    log('Verify save button is enabled')
    await expect(saveButton).not.toBeDisabled()
  });
});
