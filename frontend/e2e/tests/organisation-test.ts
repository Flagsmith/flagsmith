import {
  assertTextContent,
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.cafe'
import { E2E_USER, PASSWORD } from '../config'

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
}
