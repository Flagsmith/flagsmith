import type { Page } from '@playwright/test'
import { test, expect } from '../test-setup'
import { getFlagsmith, log, createHelpers } from '../helpers'
import {
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
  E2E_USER,
  PASSWORD,
} from '../config'

// Each test gets its own project: an environment that requires change
// requests would otherwise become the one later tests land on.
const uniqueName = (name: string) => `${name} ${Date.now()}`

const setUp = async (
  page: Page,
  projectName: string,
  { versioned = false }: { versioned?: boolean } = {},
) => {
  const helpers = createHelpers(page)
  log('Login as admin')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.createProject(projectName)
  if (versioned) await helpers.enableFeatureVersioning()
  await helpers.enableChangeRequests(1)
  return helpers
}

const createValueChangeRequest = async (
  helpers: ReturnType<typeof createHelpers>,
  featureName: string,
  value: string,
  title: string,
) => {
  await helpers.createRemoteConfig({ name: featureName, value: 'initial_value' })
  await helpers.gotoFeatures()
  await helpers.gotoFeature(featureName)
  await helpers.setText(helpers.featureValueField(), value)
  await helpers.createChangeRequest(title, `Sets ${featureName} to ${value}`)
  await helpers.closeModal()
}

const skipWithoutChangeRequests = async () => {
  const flagsmith = await getFlagsmith()
  if (!flagsmith.hasFeature('segment_change_requests')) {
    log('Skipping change request page test, feature not enabled.')
    test.skip()
  }
}

test.describe('Change Request Page', () => {
  test('A change request can be deleted from its page @enterprise', async ({
    page,
  }) => {
    await skipWithoutChangeRequests()
    const helpers = await setUp(page, uniqueName('CR Delete'))
    await createValueChangeRequest(
      helpers,
      'cr_delete_feature',
      'deleted_value',
      'Change to delete',
    )

    log('Delete it from its page')
    await helpers.gotoChangeRequests()
    await helpers.openChangeRequest(0)
    await page.getByRole('button', { name: 'Delete', exact: true }).click()
    await helpers.click('#confirm-btn-yes')

    log('Back on the list, which is now empty')
    await expect(page).toHaveURL(/\/change-requests$/)
    await helpers.assertChangeRequestCount(0)
  })

  test('Assignees can be added and removed, and stay after a reload @enterprise', async ({
    page,
  }) => {
    await skipWithoutChangeRequests()
    const helpers = await setUp(page, uniqueName('CR Assignees'))
    await createValueChangeRequest(
      helpers,
      'cr_assignee_feature',
      'assigned_value',
      'Change to assign',
    )
    await helpers.gotoChangeRequests()
    await helpers.openChangeRequest(0)

    // Seeded users have no name, so the picker row is found by email and
    // its tick shows the assignment
    const assigneeRow = () =>
      page
        .locator('.assignees-list-item')
        .filter({ hasText: E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS })
    const openUserPicker = async () => {
      await page.getByText('Assigned users').click()
      await page
        .getByPlaceholder('Search User')
        .fill(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS)
    }

    log('Assign a user')
    await openUserPicker()
    await assigneeRow().click()
    await expect(assigneeRow().locator('.font-weight-bold')).toBeVisible()

    log('The assignment is saved')
    await page.reload({ waitUntil: 'domcontentloaded' })
    await openUserPicker()
    await expect(assigneeRow().locator('.font-weight-bold')).toBeVisible()

    log('Unassign them')
    await assigneeRow().click()
    await expect(assigneeRow().locator('.font-weight-bold')).toHaveCount(0)

    log('The removal is saved')
    await page.reload({ waitUntil: 'domcontentloaded' })
    await openUserPicker()
    await expect(assigneeRow().locator('.font-weight-bold')).toHaveCount(0)
  })

  test('A change request for a deleted feature says so @enterprise', async ({
    page,
  }) => {
    await skipWithoutChangeRequests()
    const featureName = 'cr_deleted_feature'
    const helpers = await setUp(page, uniqueName('CR Deleted Feature'))
    await createValueChangeRequest(
      helpers,
      featureName,
      'orphaned_value',
      'Change for a deleted feature',
    )

    log('Open the change request while the feature still exists')
    await helpers.gotoChangeRequests()
    await helpers.openChangeRequest(0)
    await expect(page.getByText(featureName).first()).toBeVisible()

    log('Delete the feature, without a reload')
    await helpers.gotoFeatures()
    await helpers.deleteFeature(featureName)

    log('Its change request explains the feature is gone')
    await helpers.gotoChangeRequests()
    await helpers.openChangeRequest(0)
    await expect(
      page.getByText(
        'This change request contains changes for a feature that has since been deleted',
      ),
    ).toBeVisible()
    log('Nothing left to approve or publish')
    await expect(page.getByText(/approval to publish this change/)).toHaveCount(0)
  })

  test('Opening another change request shows its own changes @enterprise', async ({
    page,
  }) => {
    await skipWithoutChangeRequests()
    const helpers = await setUp(page, uniqueName('CR Switch'))
    await createValueChangeRequest(
      helpers,
      'cr_first_feature',
      'first_value',
      'First change',
    )
    await createValueChangeRequest(
      helpers,
      'cr_second_feature',
      'second_value',
      'Second change',
    )

    log('Open the first change request')
    await helpers.gotoChangeRequests()
    await page.getByText('First change', { exact: true }).click()
    await expect(page.getByText('first_value').first()).toBeVisible()

    log('Go back and open the second, without a reload')
    await helpers.gotoChangeRequests()
    await page.getByText('Second change', { exact: true }).click()
    await expect(page.getByText('second_value').first()).toBeVisible()
    await expect(page.getByText('first_value')).toHaveCount(0)
  })

  test('A change request in a versioned environment can be approved and published @enterprise', async ({
    page,
  }) => {
    await skipWithoutChangeRequests()
    const flagsmith = await getFlagsmith()
    if (!flagsmith.hasFeature('feature_versioning')) {
      log('Skipping versioned change request test, feature not enabled.')
      test.skip()
    }
    const projectName = uniqueName('CR Versioned Publish')
    const featureName = 'cr_versioned_publish_feature'
    const helpers = await setUp(page, projectName, { versioned: true })
    await createValueChangeRequest(
      helpers,
      featureName,
      'published_value',
      'Versioned change',
    )

    log('Grant the approver project ADMIN permission')
    await page.click('a:has-text("Bullet Train Ltd")')
    await helpers.setUserPermission(
      E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
      'ADMIN',
      projectName,
      'project',
    )

    log('Approve and publish as the approver')
    await helpers.logout()
    await helpers.login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
    await helpers.gotoProject(projectName)
    await helpers.gotoChangeRequests()
    await helpers.openChangeRequest(0)
    await helpers.approveChangeRequest()
    await helpers.publishChangeRequest()

    log('The feature now has the published value')
    await helpers.gotoFeatures()
    await page.reload({ waitUntil: 'domcontentloaded' })
    await helpers.gotoFeature(featureName)
    await expect(helpers.featureValueField()).toHaveText('published_value', {
      timeout: 15000,
    })
  })
})
