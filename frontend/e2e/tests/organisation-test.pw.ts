import { test, expect } from '@playwright/test';
import {
  assertTextContent,
  byId,
  click,
  closeModal,
  getText,
  log,
  login,
  setText,
  waitForElementVisible,
  waitForElementNotExist,
  clickByText,
  createHelpers,
} from '../helpers.playwright'
import { E2E_SEPARATE_TEST_USER, PASSWORD } from '../config'

test.describe('Organisation Tests', () => {
  test('test description @oss', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_SEPARATE_TEST_USER, PASSWORD)

  log('Navigate to Organisation Settings')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await helpers.click(byId('organisation-link'))
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))

  log('Edit Organisation Name')
  await helpers.waitForElementVisible("[data-test='organisation-name']")
  await helpers.setText("[data-test='organisation-name']", 'Test Organisation')
  await helpers.click('#save-org-btn')

  log('Verify Organisation Name Updated in Breadcrumb')
  await helpers.click('#projects-link')
  await assertTextContent(page, '#organisation-link', 'Test Organisation')

  log('Verify Organisation Name Persisted in Settings')
  await helpers.click(byId('organisation-link'))
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))
  await helpers.waitForElementVisible("[data-test='organisation-name']")

  log('Test 2: Create and Delete Organisation, Verify Next Org in Nav')
  log('Navigate to create organisation')
  await helpers.click(byId('home-link'))
  await helpers.waitForElementVisible(byId('create-organisation-btn'))
  await helpers.click(byId('create-organisation-btn'))

  log('Create New Organisation')
  await helpers.waitForElementVisible("[name='orgName']")
  await helpers.setText("[name='orgName']", 'E2E Test Org to Delete')
  await helpers.click('#create-org-btn')

  log('Verify New Organisation Created and appears in nav')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await assertTextContent(page, '#organisation-link', 'E2E Test Org to Delete')

  log('Navigate back to the org we want to delete')
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))

  log('Delete Organisation')
  await helpers.waitForElementVisible('#delete-org-btn')
  await helpers.click('#delete-org-btn')
  await helpers.setText("[name='confirm-org-name']", 'E2E Test Org to Delete')
  await helpers.clickByText('Confirm')

  log('Verify Redirected to Next Organisation in Nav')
  await helpers.waitForElementVisible(byId('organisation-link'))
  log('Current org in nav after deletion: Test Organisation')

  log('Verify deleted org name does not appear in nav')
  await expect(page.locator('#organisation-link')).not.toContainText('E2E Test Org to Delete')
  await assertTextContent(page, '#organisation-link', 'Test Organisation')

  log('Test 3: Cancel Organisation Deletion')
  log('Create temporary organisation for cancel test')
  await helpers.click(byId('home-link'))
  await helpers.waitForElementVisible(byId('create-organisation-btn'))
  await helpers.click(byId('create-organisation-btn'))
  await helpers.waitForElementVisible("[name='orgName']")
  await helpers.setText("[name='orgName']", 'E2E Cancel Test Org')
  await helpers.click('#create-org-btn')

  log('Navigate to org settings and open delete modal')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await assertTextContent(page, '#organisation-link', 'E2E Cancel Test Org')
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))
  await helpers.waitForElementVisible('#delete-org-btn')
  await helpers.click('#delete-org-btn')
  await helpers.waitForElementVisible("[name='confirm-org-name']")
  await helpers.setText("[name='confirm-org-name']", 'E2E Cancel Test Org')

  log('Close modal without confirming deletion')
  await closeModal(page)
  await helpers.waitForElementNotExist('.modal')

  log('Verify organisation still exists in navbar')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await assertTextContent(page, '#organisation-link', 'E2E Cancel Test Org')

  log('Clean up: Delete the test organisation')
  await helpers.click('#delete-org-btn')
  await helpers.setText("[name='confirm-org-name']", 'E2E Cancel Test Org')
  await helpers.clickByText('Confirm')
  await helpers.waitForElementNotExist('.modal')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await assertTextContent(page, '#organisation-link', 'Test Organisation')

  log('Test 4: Organisation Name Validation')
  log('Navigate to Test Organisation settings')
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))

  log('Test empty organisation name validation')
  await helpers.waitForElementVisible("[data-test='organisation-name']")
  const orgNameInput = page.locator("[data-test='organisation-name']")
  const originalName = await orgNameInput.inputValue()

  log('Clear organisation name')
  await helpers.setText("[data-test='organisation-name']", '')

  log('Verify save button is disabled')
  const saveButton = page.locator('#save-org-btn')
  await expect(saveButton).toBeDisabled()

  log('Restore original name')
  await helpers.setText("[data-test='organisation-name']", originalName)

  log('Verify save button is enabled')
  await expect(saveButton).not.toBeDisabled()
  });
});