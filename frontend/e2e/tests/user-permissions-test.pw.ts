import { test, expect } from '../test-setup'
import {
  createEnvironmentThroughApi,
  createHelpers,
  createProjectThroughApi,
  log,
} from '../helpers'
import {
  E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
  E2E_USER,
  PASSWORD,
} from '../config'

// Both dialogs list a project's environments once one is picked
const MEMBER_ACTIONS = ['Manage user', 'Inspect permissions']

test.describe('User permissions dialogs', () => {
  for (const action of MEMBER_ACTIONS) {
    test(`${action} lists only the picked project's environments @enterprise`, async ({
      page,
      request,
    }) => {
      const { login } = createHelpers(page)
      // Unique names so parallel tests and E2E_REPEAT runs never collide
      const runId = Date.now()

      log('Create two projects with their own environments')
      const first = await createProjectThroughApi(
        request,
        `Permissions A ${runId}`,
      )
      const second = await createProjectThroughApi(
        request,
        `Permissions B ${runId}`,
      )
      const firstEnvironments = [`Alpha ${runId}`, `Beta ${runId}`]
      const secondEnvironment = `Gamma ${runId}`
      for (const name of firstEnvironments) {
        await createEnvironmentThroughApi(
          request,
          first.headers,
          first.api,
          name,
          first.project.id,
        )
      }
      await createEnvironmentThroughApi(
        request,
        second.headers,
        second.api,
        secondEnvironment,
        second.project.id,
      )

      log(`Open ${action} for a member`)
      await login(E2E_USER, PASSWORD)
      await page.getByRole('link', { name: 'Users and Permissions' }).click()
      await page
        .getByRole('button', {
          name: `More actions for ${E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS}`,
        })
        .click()
      await page.getByRole('button', { name: action }).click()
      const dialog = page.getByRole('dialog')
      await dialog
        .getByRole('button', { exact: true, name: 'Environment' })
        .click()

      const pickProject = async (name: string) => {
        await dialog.getByRole('combobox').click()
        await page.getByRole('option', { exact: true, name }).click()
      }

      log('The first project lists its environments')
      await pickProject(first.project.name)
      for (const name of firstEnvironments) {
        await expect(dialog.getByText(name, { exact: true })).toBeVisible()
      }

      log('Switching project replaces the list')
      await pickProject(second.project.name)
      await expect(
        dialog.getByText(secondEnvironment, { exact: true }),
      ).toBeVisible()
      for (const name of firstEnvironments) {
        await expect(dialog.getByText(name, { exact: true })).toHaveCount(0)
      }
    })
  }
})
