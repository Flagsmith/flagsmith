import { test, expect } from '@playwright/test';
import {
  byId,
  click,
  clickByText,
  closeModal,
  createEnvironment,
  createFeature,
  editRemoteConfig,
  gotoTraits,
  log,
  login,
  logout,
  setUserPermission,
  toggleFeature,
  waitForElementClickable,
  waitForElementNotClickable,
  waitForElementNotExist,
  waitForElementVisible,
} from '../helpers/helpers';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
  E2E_USER,
} from '../config';

test('@enterprise Environment permissions test', async ({ page }) => {
  log('Login');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  
  log('User can only view project');
  await click(page, '#project-select-0');
  await expect(page.locator('#project-select-1')).not.toBeVisible();
  await logout(page);

  log('User with permissions can Handle the Features');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await createFeature(page, 0, 'test_feature', false);
  await toggleFeature(page, 0, true);
  await logout(page);

  log('User without permissions cannot create traits');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await gotoTraits(page);
  await expect(page.locator(byId('add-trait'))).toHaveAttribute('disabled', '');
  await logout(page);

  log('User without permissions cannot see audit logs');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementNotExist(page, byId('audit-log-link'));
  await logout(page);

  log('Create new environment');
  await login(page, E2E_USER, PASSWORD);
  await clickByText(page, 'My Test Project 6 Env Permission');
  await click(page, '#create-env-link');
  await createEnvironment(page, 'Production');
  await logout(page);

  log('User without permissions cannot see environment');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementVisible(page, byId('switch-environment-development'));
  await waitForElementNotExist(page, byId('switch-environment-production'));
  await logout(page);

  log('Grant view environment permission');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_ENVIRONMENT', 'Production', 'environment', 'My Test Project 6 Env Permission');
  await logout(page);

  log('User with permissions can see environment');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementVisible(page, byId('switch-environment-production'));
  await waitForElementVisible(page, byId('switch-environment-production'));
  await logout(page);

  log('User with permissions can update feature state');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await createFeature(page, 0, 'my_feature', "foo", 'A test feature');
  await editRemoteConfig(page, 0, 'bar');
  await logout(page);

  log('User without permission cannot create a segment override');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, byId('feature-item-0'));
  await click(page, byId('segment_overrides'));
  await waitForElementNotClickable(page, '#update-feature-segments-btn');
  await closeModal(page);
  await logout(page);

  log('Grant MANAGE_IDENTITIES permission');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_SEGMENT_OVERRIDES', 'Development', 'environment', 'My Test Project 6 Env Permission');
  await logout(page);

  log('User with permission can create a segment override');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, byId('feature-item-0'));
  await click(page, byId('segment_overrides'));
  await waitForElementClickable(page, '#update-feature-segments-btn');
  await closeModal(page);
  await logout(page);

  log('User without permissions cannot update feature state');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementClickable(page, byId('feature-switch-0-on'));
  await click(page, byId('switch-environment-production'));
  await waitForElementNotClickable(page, byId('feature-switch-0-on'));
  await click(page, byId('feature-item-0'));
  await waitForElementNotClickable(page, byId('update-feature-btn'));
  await closeModal(page);
  await logout(page);

  log('User with permissions can view identities');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementVisible(page, '#users-link');
  await logout(page);

  log('User without permissions cannot add user trait');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, '#users-link');
  await click(page, byId('user-item-0'));
  await waitForElementNotClickable(page, byId('add-trait'));
  await logout(page);

  log('Grant MANAGE_IDENTITIES permission');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'MANAGE_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission');
  await logout(page);

  log('User with permissions can add user trait');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, '#users-link');
  await click(page, byId('user-item-0'));
  await waitForElementClickable(page, byId('add-trait'));
  await logout(page);

  log('Remove VIEW_IDENTITIES permission');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, 'VIEW_IDENTITIES', 'Development', 'environment', 'My Test Project 6 Env Permission');
  await logout(page);

  log('User without permissions cannot view identities');
  await login(page, E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, '#users-link');
  await waitForElementVisible(page, byId('missing-view-identities'));
});
