import type { Page } from '@playwright/test'
import { test, expect } from '../test-setup'
import { createHelpers, log, LONG_TIMEOUT } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'

// Each test gets its own project, so the identities it creates are the only
// ones on the page.
const uniqueName = (name: string) => `${name} ${Date.now()}`

const setUp = async (page: Page, projectName: string) => {
  const helpers = createHelpers(page)
  log('Login as admin')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.createProject(projectName)
  return helpers
}

const gotoIdentities = async (helpers: ReturnType<typeof createHelpers>) => {
  await helpers.click('#features-link')
  await helpers.click('#users-link')
}

const identityLink = (page: Page, identifier: string) =>
  page.getByRole('link', { exact: true, name: identifier })

const createIdentities = async (page: Page, identifiers: string[]) => {
  await page.getByRole('button', { name: 'Create Identities' }).click()
  const input = page.getByPlaceholder('User1, User2, User3')
  // The placeholder goes once a chip exists, so press Enter on the focused input.
  await input.fill(identifiers.join(','))
  await page.keyboard.press('Enter')
  await page.getByRole('button', { name: 'Create users' }).click()
  for (const identifier of identifiers) {
    await expect(identityLink(page, identifier)).toBeVisible({
      timeout: LONG_TIMEOUT,
    })
  }
}

test.describe('Identities', () => {
  test('Identities can be created, searched and deleted @oss', async ({
    page,
  }) => {
    const helpers = await setUp(page, uniqueName('Identities List'))
    await gotoIdentities(helpers)

    log('Create two identities')
    await createIdentities(page, ['alice_e2e', 'bob_e2e'])

    log('Search finds one and hides the other')
    await page.getByPlaceholder('Search').fill('alice_e2e')
    await expect(identityLink(page, 'alice_e2e')).toBeVisible({
      timeout: LONG_TIMEOUT,
    })
    await expect(identityLink(page, 'bob_e2e')).toBeHidden()

    log('Loading the page directly shows the identities')
    await page.goto(page.url())
    await expect(identityLink(page, 'bob_e2e')).toBeVisible({
      timeout: LONG_TIMEOUT,
    })

    log('Delete one')
    await page.getByRole('button', { name: 'Delete identity bob_e2e' }).click()
    await page.getByRole('button', { exact: true, name: 'Confirm' }).click()
    await expect(identityLink(page, 'bob_e2e')).toBeHidden({
      timeout: LONG_TIMEOUT,
    })
    await expect(identityLink(page, 'alice_e2e')).toBeVisible()
  })

  test('An identity page loads directly and its traits can be added and removed @oss', async ({
    page,
  }) => {
    const helpers = await setUp(page, uniqueName('Identity Traits'))
    await gotoIdentities(helpers)
    await createIdentities(page, ['carol_e2e'])

    log('Open the identity')
    await identityLink(page, 'carol_e2e').click()
    await expect(
      page.getByRole('button', { name: 'Add new trait' }).first(),
    ).toBeVisible({ timeout: LONG_TIMEOUT })

    log('Loading the identity page directly shows it')
    await page.goto(page.url())
    await expect(page.getByText('carol_e2e').first()).toBeVisible({
      timeout: LONG_TIMEOUT,
    })
    await expect(
      page.getByRole('button', { name: 'Add new trait' }).first(),
    ).toBeVisible({ timeout: LONG_TIMEOUT })

    log('Add a trait, then remove it')
    await helpers.createTrait('plan', 'pro')
    await helpers.deleteTrait('plan')
  })

  test('A flag can be overridden for an identity and reset @oss', async ({
    page,
  }) => {
    const helpers = await setUp(page, uniqueName('Identity Overrides'))
    await helpers.createFeature({ name: 'identity_flag' })
    await gotoIdentities(helpers)
    await createIdentities(page, ['dave_e2e'])
    await identityLink(page, 'dave_e2e').click()

    log('The flag starts off, as in the environment')
    await helpers.waitForUserFeatureSwitch('identity_flag', 'off')

    log('Turn it on for this identity only')
    await helpers.clickUserFeatureSwitch('identity_flag', 'off')
    await page.locator('#confirm-toggle-feature-btn').click()
    await helpers.waitForUserFeatureSwitch('identity_flag', 'on')
    await expect(
      page.getByText('This feature is being overridden for this identity'),
    ).toBeVisible({ timeout: LONG_TIMEOUT })

    log('Reset it to the environment value')
    await page.getByRole('button', { name: 'Reset' }).first().click()
    const confirm = page.locator('#confirm-remove-feature-modal')
    await confirm.getByRole('textbox').fill('identity_flag')
    await confirm.getByRole('button', { name: 'Confirm' }).click()
    await helpers.waitForUserFeatureSwitch('identity_flag', 'off')
    await expect(
      page.getByText('This feature is being overridden for this identity'),
    ).toBeHidden({ timeout: LONG_TIMEOUT })
  })
})
