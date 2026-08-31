import { test, expect } from '../test-setup'
import {
  byId,
  log,
  createHelpers,
  getFlagsmith,
  LONG_TIMEOUT,
} from '../helpers'
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config'

const COHORT_PROVIDERS = ['amplitude', 'mixpanel'] as const

type CohortProvider = (typeof COHORT_PROVIDERS)[number]

type SegmentSourceFlagEntry = {
  active?: boolean
  name?: string
  visible?: boolean
}

// Mirrors `getSegmentSources` in CreateSegmentSourcesModal: only an entry that
// is visible AND active opens the connect modal (and shows the environment tab).
const getActiveCohortProviders = (config: unknown): CohortProvider[] => {
  if (!Array.isArray(config)) {
    return []
  }
  return (config as SegmentSourceFlagEntry[])
    .filter(
      (entry) =>
        COHORT_PROVIDERS.includes(entry?.name as CohortProvider) &&
        entry?.visible !== false &&
        entry?.active === true,
    )
    .map((entry) => entry.name as CohortProvider)
}

test.describe('Cohort Synchronisation Keys Tests', () => {
  test('Cohort synchronisation keys can be created from a provider connection and revoked in Environment Settings @oss', async ({
    page,
  }) => {
    const {
      click,
      gotoProject,
      gotoSegments,
      login,
      setText,
      waitForElementVisible,
      waitForModalToClose,
    } = createHelpers(page)

    const flagsmith = await getFlagsmith()
    const activeProviders = flagsmith.hasFeature(
      'create_segment_with_external_sources',
    )
      ? getActiveCohortProviders(
          flagsmith.getValue('create_segment_with_external_sources', {
            fallback: null,
            json: true,
          }),
        )
      : []
    test.skip(
      activeProviders.length === 0,
      'No active Amplitude or Mixpanel entry in `create_segment_with_external_sources`, so the cohort synchronisation UI is unreachable',
    )

    // With both providers active each key goes through a different provider;
    // with one, the second key goes through its "Create a new key" state.
    const firstProvider = activeProviders[0]
    const secondProvider = activeProviders[1] ?? activeProviders[0]

    const runId = Date.now()
    const keyOne = `e2e key one ${runId}`
    const keyTwo = `e2e key two ${runId}`
    const keyThree = `e2e key three ${runId}`

    const connectModal = page.locator('.connect-cohort-provider')
    const envSelect = connectModal.locator(byId('connect-provider-env-select'))

    const openConnectModal = async (provider: CohortProvider) => {
      await click(byId('show-create-segment-btn'))
      await click(byId(`segment-source-${provider}`))
      await waitForElementVisible(byId('connect-provider-done'))
      await expect(envSelect).toBeVisible({ timeout: LONG_TIMEOUT })
      // The modal defaults to the alphabetically first environment; assert it
      // resolved so both keys are created against the same environment.
      const label = (await envSelect.innerText()).trim()
      expect(label).not.toBe('')
      expect(label).not.toBe('Select an Environment')
      return label
    }

    const createKeyInConnectModal = async (name: string) => {
      // Step 1 renders either the create form or the existing-keys state,
      // depending on whether this environment already has keys.
      await connectModal
        .locator(
          `${byId('connect-provider-key-name')}, ${byId(
            'connect-provider-new-key',
          )}`,
        )
        .first()
        .waitFor({ state: 'visible', timeout: LONG_TIMEOUT })
      const newKeyButton = connectModal.locator(
        byId('connect-provider-new-key'),
      )
      if (await newKeyButton.isVisible()) {
        await click(byId('connect-provider-new-key'))
      }
      await setText(byId('connect-provider-key-name'), name)
      await click(byId('connect-provider-create-key'))
      await expect(
        connectModal.locator(byId('connect-provider-key-value')),
      ).toHaveValue(/.+/, { timeout: LONG_TIMEOUT })
      await click(byId('connect-provider-done'))
      await waitForModalToClose()
    }

    log('Login')
    await login(E2E_USER, PASSWORD)
    await gotoProject(E2E_TEST_PROJECT)
    await gotoSegments()

    log(`Create the first key while connecting ${firstProvider}`)
    const environmentLabel = await openConnectModal(firstProvider)
    await createKeyInConnectModal(keyOne)

    log(`Create the second key while connecting ${secondProvider}`)
    expect(await openConnectModal(secondProvider)).toBe(environmentLabel)
    await waitForElementVisible(byId('connect-provider-new-key'))
    await expect(connectModal).toContainText(keyOne)
    // This link carries the environment the modal is working against, so
    // following it guarantees we inspect the keys we just created.
    const settingsLink = connectModal.locator(
      'a[href*="tab=cohort-synchronisation"]',
    )
    await expect(settingsLink).toBeVisible()
    const settingsHref = (await settingsLink.getAttribute('href')) ?? ''
    expect(settingsHref).not.toBe('')
    await createKeyInConnectModal(keyTwo)

    log('Open the Cohort Synchronisation tab in Environment Settings')
    await page.goto(settingsHref)
    await waitForElementVisible('#cohort-sync-keys-list')
    const keysList = page.locator('#cohort-sync-keys-list')
    await expect(keysList).toContainText(keyOne)
    await expect(keysList).toContainText(keyTwo)

    log('Create a third key from Environment Settings')
    await click(byId('create-cohort-sync-key'))
    await setText(byId('cohort-sync-key-name'), keyThree)
    await click(byId('cohort-sync-key-create'))
    await expect(page.locator(byId('cohort-sync-key-value'))).toHaveValue(
      /.+/,
      { timeout: LONG_TIMEOUT },
    )
    await click(byId('cohort-sync-key-done'))
    await waitForModalToClose()
    await expect(keysList).toContainText(keyThree)

    log('Revoke every key for this environment')
    const revokeButtons = keysList.locator('[aria-label^="Revoke "]')
    for (
      let remaining = await revokeButtons.count();
      remaining > 0;
      remaining--
    ) {
      await revokeButtons.first().click()
      await click('#confirm-btn-yes')
      await expect(page.locator('#confirm-btn-yes')).toHaveCount(0, {
        timeout: LONG_TIMEOUT,
      })
      await expect(revokeButtons).toHaveCount(remaining - 1, {
        timeout: LONG_TIMEOUT,
      })
    }

    log('Verify no keys remain')
    // PanelSearch drops the list entirely and renders its empty state instead.
    await expect(page.locator('#cohort-sync-keys-list')).toHaveCount(0)
    for (const name of [keyOne, keyTwo, keyThree]) {
      await expect(page.getByText(name, { exact: true })).toHaveCount(0)
    }
  })
})
