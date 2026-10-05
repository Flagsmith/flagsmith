import { test, expect } from '../test-setup'
import {
  createHelpers,
  getFlagsmith,
  log,
  LONG_TIMEOUT,
  visualSnapshot,
} from '../helpers'
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config'

const PREREQUISITE = 'dependency_parent'
const DEPENDENT = 'dependency_child'

test.describe('Flag Dependencies', () => {
  test('A flag can be gated behind another, and says so on both sides @oss', async ({
    page,
  }, testInfo) => {
    const {
      closeModal,
      createFeature,
      deleteFeature,
      gotoFeature,
      gotoFeatures,
      gotoProject,
      login,
      toggleFeature,
      waitForModalToClose,
    } = createHelpers(page)

    const flagsmith = await getFlagsmith()
    test.skip(
      !flagsmith.hasFeature('flag_dependencies'),
      'flag_dependencies is off, so the Dependencies tab is unreachable',
    )

    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await page.waitForSelector('[name="email"]', { state: 'visible' })
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)

    log('Create the two features')
    await createFeature({ name: PREREQUISITE, value: false })
    await createFeature({ name: DEPENDENT, value: false })

    const openDependencies = async (feature: string) => {
      await gotoFeature(feature)
      await page.getByRole('button', { name: 'Dependencies' }).click()
    }

    log('The dependent has no prerequisites yet')
    await openDependencies(DEPENDENT)
    await expect(page.getByText('No prerequisites')).toBeVisible()
    await visualSnapshot(page, 'dependencies-empty', testInfo)

    log('Add the prerequisite')
    await page.getByRole('button', { name: 'Add prerequisite' }).click()
    // An E2E build swaps the Select for an input and one anchor per option.
    // The anchors carry no href, so they are not links in the accessibility
    // tree and their text is the only thing to select on.
    await page
      .locator('#create-feature-modal')
      .getByText(PREREQUISITE, { exact: true })
      .click()

    // The row standing in while the POST runs carries the same name, so pick
    // the one that has a status.
    const row = page
      .getByRole('row', { name: new RegExp(PREREQUISITE) })
      .filter({ has: page.getByRole('img', { name: /^(On|Off)$/ }) })
    await row.waitFor({ state: 'visible', timeout: LONG_TIMEOUT })

    log('The prerequisite is off, so the flag is held off')
    await expect(row.getByRole('img', { name: 'Off' })).toBeVisible()
    await expect(row.getByText('No', { exact: true })).toBeVisible()
    await expect(page.getByText(/Serving off in/)).toBeVisible()
    await visualSnapshot(page, 'dependencies-blocked', testInfo)

    log('Turning the prerequisite on satisfies it')
    await closeModal()
    await waitForModalToClose()
    await toggleFeature(PREREQUISITE, true)
    await openDependencies(DEPENDENT)
    await expect(row.getByRole('img', { name: 'On' })).toBeVisible()
    await expect(row.getByText('Yes', { exact: true })).toBeVisible()
    await expect(page.getByText(/Serving off in/)).toBeHidden()
    await visualSnapshot(page, 'dependencies-satisfied', testInfo)

    log('The prerequisite names its dependent and cannot take one of its own')
    await closeModal()
    await waitForModalToClose()
    await openDependencies(PREREQUISITE)
    await expect(
      page.getByText('Other features depend on this flag'),
    ).toBeVisible()
    await expect(
      page.getByRole('button', { name: 'Add prerequisite' }),
    ).toBeHidden()
    await expect(page.getByRole('cell', { name: DEPENDENT })).toBeVisible()
    await visualSnapshot(page, 'dependencies-dependents', testInfo)

    log('Following a dependent lands on its own Dependencies tab')
    await page.getByRole('cell', { name: DEPENDENT }).click()
    // Replacing a modal fires the outgoing one's close callback, which clears
    // the query string, so this is where the tab gets lost.
    await expect(page).toHaveURL(/tab=dependencies/)
    await expect(
      page.getByRole('row', { name: new RegExp(PREREQUISITE) }),
    ).toBeVisible()

    log('The back arrow returns to the flag that was followed from')
    const back = page.getByRole('button', {
      name: 'Back to the previous flag',
    })
    await expect(back).toBeVisible()
    await back.click()
    await expect(
      page.getByRole('cell', { name: DEPENDENT }),
    ).toBeVisible({ timeout: LONG_TIMEOUT })
    // Arrived from the list rather than from another flag, so nothing to go
    // back to.
    await expect(back).toBeHidden()

    log('Removing a prerequisite clears it from both sides')
    await closeModal()
    await waitForModalToClose()
    await openDependencies(DEPENDENT)
    await page
      .getByRole('button', { name: `Remove ${PREREQUISITE} as a prerequisite` })
      .click()
    await page.getByRole('button', { name: 'Confirm' }).click()
    await expect(page.getByText('No prerequisites')).toBeVisible({
      timeout: LONG_TIMEOUT,
    })

    // The other side loses its dependent, so it can take prerequisites again.
    await closeModal()
    await waitForModalToClose()
    await openDependencies(PREREQUISITE)
    await expect(page.getByRole('cell', { name: DEPENDENT })).toBeHidden()
    await expect(
      page.getByRole('button', { name: 'Add prerequisite' }),
    ).toBeVisible()

    log('Clean up, dependent first so the prerequisite is free to delete')
    await closeModal()
    await waitForModalToClose()
    await gotoFeatures()
    await deleteFeature(DEPENDENT)
    await deleteFeature(PREREQUISITE)
    // A half-finished teardown leaves both names taken, and the next run on
    // this project cannot create them again.
    await expect(
      page.locator('[data-test^="feature-item-"]', { hasText: DEPENDENT }),
    ).toHaveCount(0)
    await expect(
      page.locator('[data-test^="feature-item-"]', { hasText: PREREQUISITE }),
    ).toHaveCount(0)
  })
})
