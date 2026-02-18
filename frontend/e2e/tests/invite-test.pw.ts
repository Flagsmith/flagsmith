import { test } from '../test-setup';
import { byId, log, createHelpers } from '../helpers';
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config';

const invitePrefix = `flagsmith${new Date().valueOf()}`
const inviteEmail = `${invitePrefix}@restmail.net`
test.describe('Invite Tests', () => {
  test('Users can be invited, sign up, change email, and delete their account @oss', async ({ page }) => {
    const {
      assertTextContent,
      click,
      getInputValue,
      login,
      setText,
      waitForElementNotExist,
      waitForElementVisible,
    } = createHelpers(page);

    log('Login')
    await login(E2E_USER, PASSWORD)
    log('Get Invite url')
    await waitForElementVisible(byId('organisation-link'))
    await click(byId('organisation-link'))
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))
    await getInputValue(byId('organisation-name'))
    await click(byId('users-and-permissions'))
    const inviteLink = await getInputValue(byId('invite-link'))
    log('Accept invite')
    await page.goto(inviteLink)
    // Wait for the form to load
    await waitForElementVisible(byId('firstName'))
    await setText(byId('firstName'), 'Bullet')
    await setText(byId('lastName'), 'Train')
    await setText(byId('email'), inviteEmail)
    await setText(byId('password'), PASSWORD)
    await waitForElementVisible(byId('signup-btn'))
    // Wait for form validation to complete before clicking
    await page.waitForTimeout(500)
    await click(byId('signup-btn'))
    log('Change email')
    await click(byId('account-settings-link'))
    await click(byId('account-settings'))
    await click(byId('change-email-button'))
    await setText("[name='EmailAddress']", E2E_CHANGE_MAIL)
    await setText("[name='newPassword']", PASSWORD)
    await click('#save-changes')
    await waitForElementNotExist('.modal')
    await login(E2E_CHANGE_MAIL, PASSWORD)
    log('Delete invite user')
    await assertTextContent('[id=account-settings-link]', 'Account')
    await click(byId('account-settings-link'))
    await click(byId('account-settings'))
    await click(byId('delete-user-btn'))
    await setText("[name='currentPassword']", PASSWORD)
    await click(byId('delete-account'))
  });
});
