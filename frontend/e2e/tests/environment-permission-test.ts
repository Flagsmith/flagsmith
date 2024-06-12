import {
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.cafe'
import { PASSWORD, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS } from '../config'

export default async function () {
  log('Login')
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await click('#project-select-4')
  log('Create environment')
  await click('#create-env-link')
  await setText('[name="envName"]', 'Staging')
  await click('#create-env-btn')
  await waitForElementVisible(byId('switch-environment-staging-active'))
  log('Edit Environment')
  await click('#env-settings-link')
  await setText("[name='env-name']", 'Internal')
  await click('#save-env-btn')
  await waitForElementVisible(byId('switch-environment-internal-active'))
  log('Delete environment')
  await click('#delete-env-btn')
  await setText("[name='confirm-env-name']", 'Internal')
  await click('#confirm-delete-env-btn')
  await waitForElementVisible(byId('features-page'))
}
