import {
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.cafe'
import { PASSWORD, E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS } from '../config'
import { Selector, t } from 'testcafe'

export default async function () {
  const projectName = 'Test Project'
  log('Login')
  await login(E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS, PASSWORD)
  log('User without permissions cannot see any Project')
  await t
    .expect(Selector('#project-select-0').exists)
    .notOk('The element"#project-select-0" should not be present')
  log('User with permissions can Create a Project')
  await click('.btn-project-create')
  await setText(byId('projectName'), projectName)
  await click(byId('create-project-btn'))
  log('User without permissions cannot updata the Project Settings')
  await waitForElementVisible(byId('features-page'))
  await t
    .expect(Selector('#project-settings-link').exists)
    .notOk('The element #project-settings-link should not be present')
  log('User with permissions can see the Permissions')
  await click(byId('org-settings-link'))
  await click(byId('users-and-permissions'))
  await click(byId('user-0'))
  await t
    .expect(Selector('#no-organisation-permissions').exists)
    .notOk('The element #no-organisation-permissions should not be present')
  await click(byId('project-permissions-tab'))
  await waitForElementVisible(byId('permissions-list-item-0'))
  await click(byId('permissions-list-item-0'))
  await waitForElementVisible(byId('admin-switch-project'))
  await Selector(byId('admin-switch-project')).hasClass('rc-switch-checked')
  await click(byId('environment-permissions-tab'))
  log('User with permissions can see any group')
  await t.hover(Selector('body'), {
    offsetX: 300,
    offsetY: 300,
  })
  await t.click(Selector('body'))
  await waitForElementVisible(byId('tab-item-groups'))
  await click(byId('tab-item-groups'))
  await waitForElementVisible(byId('user-item-0'))
  await click(byId('user-item-0'))
  await click(byId('add-user-select'))
  await click(byId('add-user-select-option-1'))
  await click(byId('update-group-btn'))
}
