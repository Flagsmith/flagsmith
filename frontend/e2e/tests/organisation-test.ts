import {
  assertTextContent,
  byId,
  click,
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

  log(
    'Test 3: Delete Last Organisation, Verify Redirect to Create Organisation Page',
  )
  log('Navigate to organisation settings')
  await waitForElementVisible(byId('org-settings-link'))
  await click(byId('org-settings-link'))

  log('Delete Last Remaining Organisation')
  await waitForElementVisible('#delete-org-btn')
  await click('#delete-org-btn')
  await setText("[name='confirm-org-name']", 'Test Organisation')
  await clickByText('Confirm')

  log('Verify Redirected to Create Organisation Page')
  await waitForElementVisible('#create-org-page')
  log(
    'Successfully redirected to create organisation page after deleting last org',
  )
}
