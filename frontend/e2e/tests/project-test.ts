import {
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
  await click('#project-select-0')
  log('Edit Project')
  await click('#project-settings-link')
  await setText("[name='proj-name']", 'Test Project')
  await click('#save-proj-btn')
  await waitForElementVisible(byId('switch-project-test-project'))
}
