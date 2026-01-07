import { test } from '@playwright/test';
import {
  assertTextContent,
  byId,
  click,
  log,
  login,
  setText,
  waitForElementVisible,
} from '../helpers/helpers';
import { E2E_CHANGE_MAIL, E2E_USER, PASSWORD } from '../config';

test('@oss Invite and user management test', async ({ page }) => {
  const invitePrefix = `flagsmith${new Date().valueOf()}`;
  const inviteEmail = `${invitePrefix}@restmail.net`;

  log('Login');
  await login(page, E2E_USER, PASSWORD);

  log('Get Invite url');
  await waitForElementVisible(page, byId('organisation-link'));
  await click(page, byId('organisation-link'));
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));
  await page.locator(byId('organisation-name')).inputValue();
  await click(page, byId('users-and-permissions'));
  const inviteLink = await page.locator(byId('invite-link')).inputValue();

  log('Accept invite');
  await page.goto(inviteLink);
  await setText(page, '[name="email"]', inviteEmail);
  await setText(page, byId('firstName'), 'Bullet'); // visit the url
  await setText(page, byId('lastName'), 'Train');
  await setText(page, byId('email'), inviteEmail);
  await setText(page, byId('password'), PASSWORD);
  await waitForElementVisible(page, byId('signup-btn'));
  await click(page, byId('signup-btn'));

  log('Change email');
  await click(page, byId('account-settings-link'));
  await click(page, byId('change-email-button'));
  await setText(page, "[name='EmailAddress']", E2E_CHANGE_MAIL);
  await setText(page, "[name='newPassword']", PASSWORD);
  await click(page, '#save-changes');
  await login(page, E2E_CHANGE_MAIL, PASSWORD);

  log('Delete invite user');
  await assertTextContent(page, '[id=account-settings-link]', 'Account');
  await click(page, byId('account-settings-link'));
  await click(page, byId('delete-user-btn'));
  await setText(page, "[name='currentPassword']", PASSWORD);
  await click(page, byId('delete-account'));
});
