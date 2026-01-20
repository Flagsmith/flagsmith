import { test, expect } from '@playwright/test';
import {
  assertTextContent,
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers.pw'
import { Selector, t } from 'testcafe'
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config'

const invitePrefix = `flagsmith${new Date().valueOf()}`
const inviteEmail = `${invitePrefix}@restmail.net`
test.describe('TestName', () => {
  test('test description', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  log('Get Invite url')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await helpers.click(byId('organisation-link'))
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))
  await page.locator(byId('organisation-name')).value
  await helpers.click(byId('users-and-permissions'))
  const inviteLink = await page.locator(byId('invite-link')).value
  log('Accept invite')
  await navigateTo(inviteLink)
  await helpers.setText('[name="email"]', inviteEmail)
  await helpers.setText(byId('firstName'), 'Bullet') // visit the url
  await helpers.setText(byId('lastName'), 'Train')
  await helpers.setText(byId('email'), inviteEmail)
  await helpers.setText(byId('password'), PASSWORD)
  await helpers.waitForElementVisible(byId('signup-btn'))
  await helpers.click(byId('signup-btn'))
  log('Change email')
  await helpers.click(byId('account-settings-link'))
  await helpers.click(byId('change-email-button'))
  await helpers.setText("[name='EmailAddress']", E2E_CHANGE_MAIL)
  await helpers.setText("[name='newPassword']", PASSWORD)
  await helpers.click('#save-changes')
  await helpers.login(E2E_CHANGE_MAIL, PASSWORD)
  log('Delete invite user')
  await assertTextContent('[id=account-settings-link]', 'Account')
  await helpers.click(byId('account-settings-link'))
  await helpers.click(byId('delete-user-btn'))
  await helpers.setText("[name='currentPassword']", PASSWORD)
  await helpers.click(byId('delete-account'))
  });
});