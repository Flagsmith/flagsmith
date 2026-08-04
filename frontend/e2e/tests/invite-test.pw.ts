import { test, expect } from '../test-setup';
import { byId, log, createHelpers, LONG_TIMEOUT } from '../helpers';
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config';

const invitePrefix = `flagsmith${new Date().valueOf()}`
const inviteEmail = `${invitePrefix}@restmail.net`
test.describe('Invite Tests', () => {
  test('Users can be invited, sign up, change email, and delete their account @oss', async ({ page }) => {
    const {
      assertTextContent,
      click,
      clickByText,
      getInputValue,
      gotoAccountSettings,
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
    // Wait for invite links section to load, then try to get invite link
    // ADMIN link may not exist after teardown, fall back to User role
    const hasAdminLink = await page.locator(byId('invite-link')).waitFor({ state: 'visible', timeout: 5000 }).then(() => true).catch(() => false)
    if (!hasAdminLink) {
      await click(byId('invite-role-select-option-1'))
      await waitForElementVisible(byId('invite-link'))
    }
    const inviteLink = await getInputValue(byId('invite-link'))
    log('Accept invite')
    await page.goto(inviteLink)
    // Wait for the form to load
    await waitForElementVisible(byId('firstName'))
    // Invitees who already have an account can only get in by logging in.
    await expect(page.getByRole('link', { name: 'Log in', exact: true })).toBeVisible()
    await setText(byId('firstName'), 'Bullet')
    await setText(byId('lastName'), 'Train')
    await setText(byId('email'), inviteEmail)
    await setText(byId('password'), PASSWORD)
    // Enabled, not just visible: the button stays disabled until the password
    // requirements pass.
    await expect(page.locator(byId('signup-btn'))).toBeEnabled()
    await click(byId('signup-btn'))
    log('Change email')
    await gotoAccountSettings()
    await click(byId('change-email-button'))
    await setText("[name='EmailAddress']", E2E_CHANGE_MAIL)
    await setText("[name='newPassword']", PASSWORD)
    await click('#save-changes')
    await expect(page.locator('.modal')).toHaveCount(0, { timeout: LONG_TIMEOUT })
    await login(E2E_CHANGE_MAIL, PASSWORD)
    log('Delete invite user')
    await assertTextContent('[id=account-settings-link]', 'Account')
    await gotoAccountSettings()
    await click(byId('delete-user-btn'))
    await setText("[name='currentPassword']", PASSWORD)
    await click(byId('delete-account'))
  });

  test('Signup sends users to login when their email already has an account @oss', async ({ page }) => {
    const { click, setText, waitForElementVisible } = createHelpers(page);

    log('Open signup')
    await page.goto('/signup')
    await waitForElementVisible(byId('firstName'))
    await expect(page.getByRole('link', { name: 'Log in', exact: true })).toBeVisible()

    log('Sign up with an email that already has an account')
    await setText(byId('firstName'), 'Existing')
    await setText(byId('lastName'), 'User')
    await setText(byId('email'), E2E_USER)
    await setText(byId('password'), PASSWORD)
    // Enabled, not just visible: the button stays disabled until the password
    // requirements pass.
    await expect(page.locator(byId('signup-btn'))).toBeEnabled()
    await click(byId('signup-btn'))

    log('Sent to login, prefilled, with the reason at the top')
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByText('You already have an account')).toBeVisible()
    await expect(page.locator(byId('email'))).toHaveValue(E2E_USER)
  });
});
