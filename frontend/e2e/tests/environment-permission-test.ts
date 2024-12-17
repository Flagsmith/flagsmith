import {
  byId,
  click, clickByText, createEnvironment,
  createFeature,
  gotoTraits,
  log,
  login, logout,
  toggleFeature, waitForElementNotExist, waitForElementVisible,
} from '../helpers.cafe';
import { PASSWORD, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, E2E_USER } from '../config';
import { Selector, t } from 'testcafe'

export default async function () {
  log('Login')
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  log('User only can see an project')
  await click('#project-select-0')
  await t
    .expect(Selector('#project-select-1').exists)
    .notOk('The element"#project-select-1" should not be present')
  await logout()

  log('User with permissions can Handle the Features')
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await click('#project-select-0')
  await createFeature(0, 'test_feature', false)
  await toggleFeature(0, true)
  await logout()

  log('User without permissions cannot create traits')
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await click('#project-select-0')
  await gotoTraits()
  const createTraitBtn = Selector(byId('add-trait'))
  await t.expect(createTraitBtn.hasAttribute('disabled')).ok()
  await logout()

  log('User without permissions cannot see audit logs')
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await click('#project-select-0')
  await waitForElementNotExist(byId('audit-log-link'))
  await logout()

  log('Create new environment')
  await login(E2E_USER, PASSWORD)
  await clickByText('My Test Project 6 Env Permission')
  await createEnvironment('Production')
  await logout()
  log('User without permissions cannot see environment')
  await waitForElementNotExist(byId('audit-log-link'))
  await login(E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD)
  await click('#project-select-0')
  await waitForElementVisible(byId('switch-environment-development'))
  await waitForElementNotExist(byId('switch-environment-production'))
}
