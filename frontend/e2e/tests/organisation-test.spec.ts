import { test, expect } from '@playwright/test';
import {
  assertTextContent,
  byId,
  click,
  closeModal,
  clickByText,
  log,
  login,
  setText,
  waitForElementVisible,
  waitForElementNotExist,
} from '../helpers/helpers';
import { E2E_SEPARATE_TEST_USER, PASSWORD } from '../config';

test('@oss Organisation settings test', async ({ page }) => {
  log('Login');
  await login(page, E2E_SEPARATE_TEST_USER, PASSWORD);

  log('Navigate to Organisation Settings');
  await waitForElementVisible(page, byId('organisation-link'));
  await click(page, byId('organisation-link'));
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));

  log('Edit Organisation Name');
  await waitForElementVisible(page, "[data-test='organisation-name']");
  await setText(page, "[data-test='organisation-name']", 'Test Organisation');
  await click(page, '#save-org-btn');

  log('Verify Organisation Name Updated in Breadcrumb');
  await click(page, '#projects-link');
  await assertTextContent(page, '#organisation-link', 'Test Organisation');

  log('Verify Organisation Name Persisted in Settings');
  await click(page, byId('organisation-link'));
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));
  await waitForElementVisible(page, "[data-test='organisation-name']");

  log('Test 2: Create and Delete Organisation, Verify Next Org in Nav');
  log('Navigate to create organisation');
  await click(page, byId('home-link'));
  await waitForElementVisible(page, byId('create-organisation-btn'));
  await click(page, byId('create-organisation-btn'));

  log('Create New Organisation');
  await waitForElementVisible(page, "[name='orgName']");
  await setText(page, "[name='orgName']", 'E2E Test Org to Delete');
  await click(page, '#create-org-btn');

  log('Verify New Organisation Created and appears in nav');
  await waitForElementVisible(page, byId('organisation-link'));
  await assertTextContent(page, '#organisation-link', 'E2E Test Org to Delete');

  log('Navigate back to the org we want to delete');
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));

  log('Delete Organisation');
  await waitForElementVisible(page, '#delete-org-btn');
  await click(page, '#delete-org-btn');
  await setText(page, "[name='confirm-org-name']", 'E2E Test Org to Delete');
  await clickByText(page, 'Confirm');

  log('Verify Redirected to Next Organisation in Nav');
  await waitForElementVisible(page, byId('organisation-link'));
  log('Current org in nav after deletion: Test Organisation');

  log('Verify deleted org name does not appear in nav');
  const orgLink = page.locator('#organisation-link');
  await expect(orgLink).not.toContainText('E2E Test Org to Delete');
  await assertTextContent(page, '#organisation-link', 'Test Organisation');

  log('Test 3: Cancel Organisation Deletion');
  log('Create temporary organisation for cancel test');
  await click(page, byId('home-link'));
  await waitForElementVisible(page, byId('create-organisation-btn'));
  await click(page, byId('create-organisation-btn'));
  await waitForElementVisible(page, "[name='orgName']");
  await setText(page, "[name='orgName']", 'E2E Cancel Test Org');
  await click(page, '#create-org-btn');

  log('Navigate to org settings and open delete modal');
  await waitForElementVisible(page, byId('organisation-link'));
  await assertTextContent(page, '#organisation-link', 'E2E Cancel Test Org');
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));
  await waitForElementVisible(page, '#delete-org-btn');
  await click(page, '#delete-org-btn');
  await waitForElementVisible(page, "[name='confirm-org-name']");
  await setText(page, "[name='confirm-org-name']", 'E2E Cancel Test Org');

  log('Close modal without confirming deletion');
  await closeModal(page);
  await waitForElementNotExist(page, '.modal');

  log('Verify organisation still exists in navbar');
  await waitForElementVisible(page, byId('organisation-link'));
  await assertTextContent(page, '#organisation-link', 'E2E Cancel Test Org');

  log('Clean up: Delete the test organisation');
  await click(page, '#delete-org-btn');
  await setText(page, "[name='confirm-org-name']", 'E2E Cancel Test Org');
  await clickByText(page, 'Confirm');
  await waitForElementNotExist(page, '.modal');
  await waitForElementVisible(page, byId('organisation-link'));
  await assertTextContent(page, '#organisation-link', 'Test Organisation');

  log('Test 4: Organisation Name Validation');
  log('Navigate to Test Organisation settings');
  await waitForElementVisible(page, byId('org-settings-link'));
  await click(page, byId('org-settings-link'));

  log('Test empty organisation name validation');
  await waitForElementVisible(page, "[data-test='organisation-name']");
  const orgNameInput = page.locator("[data-test='organisation-name']");
  const originalName = await orgNameInput.inputValue();

  log('Clear organisation name');
  await setText(page, "[data-test='organisation-name']", '');

  log('Verify save button is disabled');
  const saveButton = page.locator('#save-org-btn');
  await expect(saveButton).toBeDisabled();

  log('Restore original name');
  await setText(page, "[data-test='organisation-name']", originalName);

  log('Verify save button is enabled');
  await expect(saveButton).toBeEnabled();
});
