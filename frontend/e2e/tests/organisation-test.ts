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
  clickByText,
} from '../helpers.cafe'
import { E2E_USER, PASSWORD } from '../config'
import { Selector, t } from 'testcafe'

export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)

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

  log('Verify New Organisation Created and appears in nav')
  await waitForElementVisible(byId('organisation-link'))
  await assertTextContent('#organisation-link', 'E2E Test Org to Delete')

  log('Navigate back to the org we want to delete')
  await waitForElementVisible(byId('org-settings-link'))
  await click(byId('org-settings-link'))

  log('Delete Organisation')
  await waitForElementVisible('#delete-org-btn')
  await click('#delete-org-btn')
  await setText("[name='confirm-org-name']", 'E2E Test Org to Delete')
  await clickByText('Confirm')

  log('Verify Redirected to Next Organisation in Nav')
  await waitForElementVisible(byId('organisation-link'))
  log('Current org in nav after deletion: Test Organisation')

  log('Verify deleted org name does not appear in nav')
  const orgLink = Selector('#organisation-link')
  await t
    .expect(orgLink.textContent)
    .notContains(
      'E2E Test Org to Delete',
      'Deleted organisation should not appear in nav',
    )
  await assertTextContent('#organisation-link', 'Test Organisation')

  log('Test 3: Cancel Organisation Deletion')
  log('Create temporary organisation for cancel test')
  await click(byId('home-link'))
  await waitForElementVisible(byId('create-organisation-btn'))
  await click(byId('create-organisation-btn'))
  await waitForElementVisible("[name='orgName']")
  await setText("[name='orgName']", 'E2E Cancel Test Org')
  await click('#create-org-btn')

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
  await click('#delete-org-btn')
  await setText("[name='confirm-org-name']", 'E2E Cancel Test Org')
  await clickByText('Confirm')
  await waitForElementVisible(byId('organisation-link'))
  await assertTextContent('#organisation-link', 'Test Organisation')

  log('Test 4: Organisation Name Validation')
  log('Navigate to Test Organisation settings')
  await waitForElementVisible(byId('org-settings-link'))
  await click(byId('org-settings-link'))

  log('Test empty organisation name validation')
  await waitForElementVisible("[data-test='organisation-name']")
  const orgNameInput = Selector("[data-test='organisation-name']")
  const originalName = await orgNameInput.value

  log('Clear organisation name')
  await setText("[data-test='organisation-name']", '')

  log('Verify save button is disabled')
  const saveButton = Selector('#save-org-btn')
  await t
    .expect(saveButton.hasAttribute('disabled'))
    .ok('Save button should be disabled with empty name')

  log('Restore original name')
  await setText("[data-test='organisation-name']", originalName)

  log('Verify save button is enabled')
  await t
    .expect(saveButton.hasAttribute('disabled'))
    .notOk('Save button should be enabled with valid name')
}
