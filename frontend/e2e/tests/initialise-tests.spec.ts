import { test } from '@playwright/test';
import {
  byId,
  click,
  log,
  setText,
  waitForElementVisible,
} from '../helpers/helpers';
import { E2E_SIGN_UP_USER, PASSWORD } from '../config';

test('@oss Initial setup test', async ({ page }) => {
  log('Create Organisation');
  await click(page, byId('jsSignup'));
  await setText(page, byId('firstName'), 'Bullet');
  await setText(page, byId('lastName'), 'Train');
  await setText(page, byId('email'), E2E_SIGN_UP_USER);
  await setText(page, byId('password'), PASSWORD);
  await click(page, byId('signup-btn'));
  await setText(page, '[name="orgName"]', 'Flagsmith Ltd 0');
  await click(page, '#create-org-btn');
  await waitForElementVisible(page, byId('project-manage-widget'));

  log('Create Project');
  await click(page, byId('create-first-project-btn'));
  await setText(page, byId('projectName'), 'My Test Project');
  await click(page, byId('create-project-btn'));
  await waitForElementVisible(page, byId('features-page'));

  log('Hide disabled flags');
  await click(page, '#project-link');
  await click(page, '#project-settings-link');
  await click(page, byId('js-sdk-settings'));
  await click(page, byId('js-hide-disabled-flags'));
  await setText(page, byId('js-project-name'), 'My Test Project');
  await click(page, byId('js-confirm'));
});
