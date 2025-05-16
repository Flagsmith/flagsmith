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
import { E2E_USER, PASSWORD } from '../config';

test('@oss Project settings test', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-0');
  
  log('Edit Project');
  await click(page, '#project-link');
  await click(page, '#project-settings-link');
  await setText(page, "[name='proj-name']", 'Test Project');
  await click(page, '#save-proj-btn');
  await assertTextContent(page, '#project-link', 'Test Project');
});
