import { test, expect } from '../test-setup'
import { createHelpers, log } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'

test.describe('Management API keys', () => {
  test('can create, edit, and delete a role-scoped key @enterprise', async ({
    page,
  }) => {
    const roleName = 'management_api_key_e2e_role'
    const apiKeyName = 'Management API key E2E'
    const updatedApiKeyName = `${apiKeyName} updated`
    const { login } = createHelpers(page)

    log('Login')
    await login(E2E_USER, PASSWORD)

    const organisationLink = page.getByRole('link', {
      name: 'Bullet Train Ltd',
    })
    await organisationLink.waitFor({ state: 'visible' })
    await organisationLink.click()

    await page.getByRole('link', { name: 'Users and Permissions' }).click()
    await page.getByRole('button', { name: 'Roles', exact: true }).click()
    await page.getByRole('button', { name: 'Create Role', exact: true }).click()

    const roleDialog = page.getByRole('dialog')
    await roleDialog.getByRole('textbox', { name: 'Name' }).fill(roleName)
    await roleDialog
      .getByRole('button', { name: 'Create', exact: true })
      .click()
    await expect(page.getByText(roleName, { exact: true })).toBeVisible()

    await page.getByRole('link', { name: 'Organisation Settings' }).click()
    await page.getByRole('button', { name: 'API Access', exact: true }).click()
    await page
      .getByRole('button', { name: 'Create API Key', exact: true })
      .click()

    const apiKeyDialog = page.getByRole('dialog')
    await apiKeyDialog.getByRole('textbox', { name: 'Name' }).fill(apiKeyName)
    await apiKeyDialog.getByRole('switch', { name: 'Is admin' }).click()
    await apiKeyDialog
      .getByRole('button', { name: 'Select roles', exact: true })
      .click()

    const roleOption = page.getByText(roleName, { exact: true }).last()
    await roleOption.click()
    await expect(
      apiKeyDialog.locator('.chip').filter({ hasText: roleName }),
    ).toHaveCount(1)
    await apiKeyDialog
      .getByRole('button', { name: 'Select roles', exact: true })
      .click()
    await apiKeyDialog
      .getByRole('textbox', { name: 'Expiry' })
      .fill('12/31/2099')
    await apiKeyDialog.getByRole('textbox', { name: 'Expiry' }).press('Enter')
    await expect(
      apiKeyDialog.getByRole('button', { name: 'Clear Date' }),
    ).toBeEnabled()

    await apiKeyDialog
      .getByRole('button', { name: 'Create', exact: true })
      .click()
    await expect(
      apiKeyDialog.getByText('Your key has been created.', { exact: false }),
    ).toBeVisible()
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: 'Confirm', exact: true }).click()
    await expect(page.locator('.modal-open')).toHaveCount(0)

    const editButton = page.getByRole('button', {
      name: `Edit API key ${apiKeyName}`,
    })
    await expect(editButton).toBeVisible()
    await editButton.click()

    const editDialog = page.getByRole('dialog')
    await expect(editDialog.getByRole('textbox', { name: 'Name' })).toHaveValue(
      apiKeyName,
    )
    await expect(
      editDialog.locator('.chip').filter({ hasText: roleName }),
    ).toHaveCount(1)
    await editDialog
      .getByRole('button', { name: 'Select roles', exact: true })
      .click()
    const editRoleOption = page.getByText(roleName, { exact: true }).last()
    await editRoleOption.click()
    await expect(
      editDialog.locator('.chip').filter({ hasText: roleName }),
    ).toHaveCount(0)
    await editRoleOption.click()
    await expect(
      editDialog.locator('.chip').filter({ hasText: roleName }),
    ).toHaveCount(1)
    await editDialog
      .getByRole('button', { name: 'Select roles', exact: true })
      .click()
    await editDialog
      .getByRole('textbox', { name: 'Name' })
      .fill(updatedApiKeyName)
    await expect(
      editDialog.getByRole('textbox', { name: 'Expiry' }),
    ).not.toHaveValue('Never')
    await editDialog
      .getByRole('button', { name: 'Update', exact: true })
      .click()
    await expect(
      page.getByRole('button', { name: `Edit API key ${updatedApiKeyName}` }),
    ).toBeVisible()

    await page
      .getByRole('button', { name: `Delete API key ${updatedApiKeyName}` })
      .click()
    await page.getByRole('button', { name: 'Confirm', exact: true }).click()
    await expect(
      page.getByRole('button', { name: `Edit API key ${updatedApiKeyName}` }),
    ).toHaveCount(0)
  })
})
