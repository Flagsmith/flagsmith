import { test, expect } from '@playwright/test';
import {
  byId,
  click,
  createEnvironment,
  createFeature,
  gotoSegments,
  log,
  login,
  logout,
  setUserPermission,
  toggleFeature,
  waitForElementNotClickable,
  waitForElementNotExist,
  waitForElementVisible,
} from '../helpers/helpers';
import { E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, E2E_USER, PASSWORD } from '../config';

test('@enterprise Project permissions test', async ({ page }) => {
  log('User with VIEW_PROJECT can only see their project');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await waitForElementNotExist(page, '#project-select-1');
  await logout(page);

  log('User with CREATE_ENVIRONMENT can create an environment');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await createEnvironment(page, 'Staging');
  await logout(page);

  log('User with VIEW_AUDIT_LOG can view the audit log');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, byId('audit-log-link'));
  await logout(page);

  log('Remove VIEW_AUDIT_LOG permission');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'VIEW_AUDIT_LOG', 'My Test Project 5 Project Permission', 'project');
  await logout(page);

  log('User without VIEW_AUDIT_LOG cannot view the audit log');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementNotExist(page, 'audit-log-link');
  await logout(page);

  log('User with CREATE_FEATURE can Handle the Features');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await createFeature(page, 0, 'test_feature', false);
  await toggleFeature(page, 0, true);
  await logout(page);

  log('Remove CREATE_FEATURE permissions');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_FEATURE', 'My Test Project 5 Project Permission', 'project');
  await logout(page);

  log('User without CREATE_FEATURE cannot Handle the Features');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementNotClickable(page, '#show-create-feature-btn');
  await logout(page);

  log('User without ADMIN permissions cannot set other users project permissions');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await waitForElementNotExist(page, '#project-settings-link');
  await logout(page);

  log('Set user as project ADMIN');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project');
  await logout(page);

  log('User with ADMIN permissions can set project settings');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementVisible(page, '#project-settings-link');
  await logout(page);

  log('Remove user as project ADMIN');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'ADMIN', 'My Test Project 5 Project Permission', 'project');
  await logout(page);

  log('User without create environment permissions cannot create a new environment');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'CREATE_ENVIRONMENT', 'My Test Project 5 Project Permission', 'project');
  await logout(page);
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await waitForElementNotExist(page, '#create-env-link');
  await logout(page);

  log('User without DELETE_FEATURE permissions cannot Delete any feature');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, byId('feature-action-0'));
  await waitForElementVisible(page, byId('remove-feature-btn-0'));
  await expect(page.locator(byId('remove-feature-btn-0'))).toHaveClass(/feature-action__item_disabled/);
  await logout(page);

  log('Add DELETE_FEATURE permission to user');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, 'DELETE_FEATURE', 'My Test Project 5 Project Permission', 'project');
  await logout(page);

  log('User with permissions can Delete any feature');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await click(page, byId('feature-action-0'));
  await waitForElementVisible(page, byId('remove-feature-btn-0'));
  await expect(page.locator(byId('remove-feature-btn-0'))).not.toHaveClass(/feature-action__item_disabled/);
  await logout(page);

  log('User without MANAGE_SEGMENTS permissions cannot Manage Segments');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await gotoSegments(page);
  await expect(page.locator(byId('show-create-segment-btn'))).toHaveAttribute('disabled', '');
  await logout(page);

  log('Add MANAGE_SEGMENTS permission to user');
  await login(page, E2E_USER, PASSWORD);
  await setUserPermission(
    page,
    E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
    'MANAGE_SEGMENTS',
    'My Test Project 5 Project Permission',
    'project'
  );
  await logout(page);

  log('User with MANAGE_SEGMENTS permissions can Manage Segments');
  await login(page, E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD);
  await click(page, '#project-select-0');
  await gotoSegments(page);
  await expect(page.locator(byId('show-create-segment-btn'))).not.toHaveAttribute('disabled', '');
});
