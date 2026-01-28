import { test, expect } from '../test-setup';
import { byId, log, createHelpers } from '../helpers.playwright';
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS,
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
} from '../config';

test.describe('Organisation Permission Tests', () => {
  test('test description @enterprise', async ({ page }) => {
    const {
      click,
      clickByText,
      login,
      logout,
      waitForElementClickable,
      waitForElementNotClickable,
    } = createHelpers(page);

    log('Login')
    await login(E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS, PASSWORD)
    log('User without permissions cannot see any Project')
    await expect(page.locator('#project-select-0')).not.toBeVisible()
    log('User with permissions can Create a Project')
    await waitForElementClickable(byId('create-first-project-btn'))

    log('User can manage groups')
    await click(byId('users-and-permissions'))
    await clickByText('Groups')
    await waitForElementClickable("#btn-invite-groups")
    await logout()
    log('Login as project user')
    await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    log('User cannot manage users or groups')
    await click(byId('users-and-permissions'))
    await clickByText('Groups')
    await waitForElementNotClickable("#btn-invite-groups")
  });
});