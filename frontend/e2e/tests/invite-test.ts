import {
  assertTextContent,
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.cafe'
import { Selector, t } from 'testcafe'
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config'

const invitePrefix = `flagsmith${new Date().valueOf()}`
const inviteEmail = `${invitePrefix}@restmail.net`
export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)
  log('Get Invite url')
  await waitForElementVisible(byId('organisation-link'))
  await click(byId('organisation-link'))
  await waitForElementVisible(byId('org-settings-link'))
  await click(byId('org-settings-link'))
  await Selector(byId('organisation-name')).value
  await click(byId('users-and-permissions'))
  const inviteLink = await Selector(byId('invite-link')).value
  log('Accept invite')
  await t.navigateTo(inviteLink)
  await setText('[name="email"]', inviteEmail)
  await setText(byId('firstName'), 'Bullet') // visit the url
  await setText(byId('lastName'), 'Train')
  await setText(byId('email'), inviteEmail)
  await setText(byId('password'), PASSWORD)
  await waitForElementVisible(byId('signup-btn'))
  await click(byId('signup-btn'))
  log('Change email')
  await click(byId('account-settings-link'))
  await click(byId('change-email-button'))
  await setText("[name='EmailAddress']", E2E_CHANGE_MAIL)
  await setText("[name='newPassword']", PASSWORD)
  await click('#save-changes')
  await login(E2E_CHANGE_MAIL, PASSWORD)
  log('Delete invite user')
  await assertTextContent('[id=account-settings-link]', 'Account')
  await click(byId('account-settings-link'))
  await click(byId('delete-user-btn'))
  await setText("[name='currentPassword']", PASSWORD)
  await click(byId('delete-account'))
}
