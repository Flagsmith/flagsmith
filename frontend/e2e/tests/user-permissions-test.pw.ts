import { test, expect } from '../test-setup'
import { createHelpers, log } from '../helpers'
import {
  E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
  E2E_USER,
  PASSWORD,
} from '../config'

// Seeded projects: the first has Development and Production, the second only Development
const PROJECT_WITH_TWO_ENVIRONMENTS = 'My Test Project'
const PROJECT_WITH_ONE_ENVIRONMENT = 'My Test Project 2'

const MEMBER_ACTIONS = ['Manage user', 'Inspect permissions']

test.describe('User permissions dialogs', () => {
  for (const action of MEMBER_ACTIONS) {
    test(`${action} lists only the picked project's environments @enterprise`, async ({
      page,
    }) => {
      const { login } = createHelpers(page)

      log(`Open ${action} for a member`)
      await login(E2E_USER, PASSWORD)
      await page.getByRole('link', { name: 'Users and Permissions' }).click()
      await page
        .getByRole('button', {
          name: `More actions for ${E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS}`,
        })
        .click()
      // The menu items aren't buttons yet
      await page.getByText(action, { exact: true }).click()
      const dialog = page.getByRole('dialog')
      await dialog
        .getByRole('button', { exact: true, name: 'Environment' })
        .click()

      const pickProject = async (name: string) => {
        await dialog.getByRole('combobox', { name: 'Project' }).click()
        await page.getByRole('option', { name, exact: true }).click()
      }

      log('A project lists its environments')
      await pickProject(PROJECT_WITH_ONE_ENVIRONMENT)
      await expect(
        dialog.getByText('Development', { exact: true }),
      ).toBeVisible()

      log("Switching project loads the new project's list")
      await pickProject(PROJECT_WITH_TWO_ENVIRONMENTS)
      await expect(
        dialog.getByText('Production', { exact: true }),
      ).toBeVisible()
    })
  }
})
