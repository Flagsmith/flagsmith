import { test } from '../test-setup';
import { assertTextContent, byId, createHelpers, getInputValue, log } from '../helpers.playwright';
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config';

const invitePrefix = `flagsmith${new Date().valueOf()}`
const inviteEmail = `${invitePrefix}@restmail.net`
test.describe('Invite Tests', () => {
  test('test description @oss', async ({ page }) => {
    const helpers = createHelpers(page);
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  log('Get Invite url')
  await helpers.waitForElementVisible(byId('organisation-link'))
  await helpers.click(byId('organisation-link'))
  await helpers.waitForElementVisible(byId('org-settings-link'))
  await helpers.click(byId('org-settings-link'))
  await getInputValue(page, byId('organisation-name'))
  await helpers.click(byId('users-and-permissions'))
  const inviteLink = await getInputValue(page, byId('invite-link'))
  log('Accept invite')
  await page.goto(inviteLink)
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
  await helpers.waitForElementNotExist('.modal')
  await helpers.login(E2E_CHANGE_MAIL, PASSWORD)
  log('Delete invite user')
  await assertTextContent(page, '[id=account-settings-link]', 'Account')
  await helpers.click(byId('account-settings-link'))
  await helpers.click(byId('delete-user-btn'))
  await helpers.setText("[name='currentPassword']", PASSWORD)
  await helpers.click(byId('delete-account'))
  });
});
