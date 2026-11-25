import { Page } from '@playwright/test'
import { test, expect } from '../test-setup'
import { byId, createHelpers, isSaas, log, visualSnapshot } from '../helpers'
import { E2E_PROJECT_WITH_EXPERIMENTS, E2E_USER, PASSWORD } from '../config'

const FEATURE = 'experiment_checkout'
const METRIC = 'Checkout conversion'
const FIRST_EXPERIMENT = 'Checkout redesign'

// The steps build on each other: the warehouse and metric feed the experiment.
test.describe.configure({ mode: 'serial' })

const setup = async (page: Page) => {
  const helpers = createHelpers(page)
  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.gotoProject(E2E_PROJECT_WITH_EXPERIMENTS)
  await helpers.waitForElementVisible(byId('features-page'))
  return helpers
}

const gotoExperiments = async (page: Page) => {
  const { click, waitForElementVisible } = createHelpers(page)
  await click('#experiments-link')
  await waitForElementVisible(byId('experiments-page'))
}

const experimentRow = (page: Page, name: string) =>
  page.locator('.experiments-table__row').filter({ hasText: name })

const createExperiment = async (page: Page, name: string) => {
  const { click, clickByText, setText, waitForElementVisible, waitForToast } =
    createHelpers(page)
  await gotoExperiments(page)
  await clickByText('Create Experiment')

  log('Setup step')
  await setText('input[placeholder="e.g. Checkout Button Redesign"]', name)
  await setText(
    'textarea[placeholder^="e.g. Redesigning the checkout button"]',
    'A clearer checkout increases conversion',
  )
  await page.getByRole('combobox', { name: 'Feature Flag' }).click()
  await page.getByRole('option', { name: FEATURE, exact: true }).click()
  await click('#experiment-wizard-setup-continue')

  log('Rollout step: all users, even split')
  await click('#experiment-wizard-rollout-continue')

  log('Measurement step')
  await page.locator('.metric-select-list').getByText(METRIC).click()
  await click('#experiment-wizard-measurement-continue')

  log('Review step')
  await click('#experiment-wizard-review-create')
  await click('#confirm-btn-yes')
  await waitForToast()
  await waitForElementVisible('.experiments-table')
}

const rolloutOverride = (page: Page) =>
  page.locator('#create-feature-modal').getByText('Managed by an experiment')

// The segment picker renders once the overrides have loaded and the feature
// is no longer frozen, so an absent override is not a list still loading.
const expectNoRolloutOverride = async (page: Page) => {
  await createHelpers(page).waitForElementVisible(byId('select-segment'))
  await expect(rolloutOverride(page)).toHaveCount(0)
}

const skipOnSaas = async () => {
  test.skip(
    await isSaas(),
    'The Flagsmith database warehouse is only offered on self-hosted',
  )
}

test.describe('Experimentation Tests', () => {
  test('Warehouse can be connected and a metric created @oss', async ({
    page,
  }, testInfo) => {
    await skipOnSaas()
    const { click, setText, waitForElementVisible, waitForToast } = await setup(
      page,
    )

    log('Connect the Flagsmith database warehouse')
    await click('#env-settings-link')
    await page.goto(`${page.url().split('?')[0]}?tab=warehouse`)
    await click('#warehouse-enable-flagsmith-database')
    await click('#confirm-btn-yes')
    await waitForToast()
    await waitForElementVisible(byId('warehouse-connection-status-connected'))
    await expect(
      page.getByText('Flagsmith database (PostgreSQL)'),
    ).toBeVisible()
    await visualSnapshot(page, 'experimentation-warehouse-connected', testInfo)

    log('Create a metric')
    await click('#metrics-link')
    await click('#metrics-page-create-empty')
    await setText('#metric-name', METRIC)
    await page.locator('#metric-event').fill('checkout_completed')
    await page.keyboard.press('Enter')
    await click('#metric-form-submit')
    await waitForToast()
    await waitForElementVisible(byId('metrics-page'))
    await expect(page.getByText(METRIC)).toBeVisible()
    await expect(page.getByText('checkout_completed')).toBeVisible()
  })

  test('Experiment can be created and freezes the feature value @oss', async ({
    page,
  }, testInfo) => {
    await skipOnSaas()
    const { click, closeModal, featureValueField, gotoFeature, gotoFeatures } =
      await setup(page)

    log('Create an experiment')
    await createExperiment(page, FIRST_EXPERIMENT)
    await expect(experimentRow(page, FIRST_EXPERIMENT)).toContainText('Running')
    await visualSnapshot(page, 'experimentation-experiment-running', testInfo)

    log('The feature value is frozen while the experiment runs')
    await gotoFeatures()
    await gotoFeature(FEATURE)
    await expect(page.locator('#create-feature-modal')).toContainText(
      `This flag is part of the experiment ${FIRST_EXPERIMENT}`,
    )
    await expect(featureValueField()).not.toBeEditable()
    await click(byId('segment_overrides'))
    await expect(rolloutOverride(page)).toHaveCount(1)
    await closeModal()
  })

  test('Experiment can be completed by rolling out a variant @oss', async ({
    page,
  }, testInfo) => {
    await skipOnSaas()
    const {
      click,
      clickByText,
      closeModal,
      gotoFeature,
      gotoFeatures,
      waitForToast,
    } = await setup(page)

    log('Complete the experiment rolling out variant_b')
    await gotoExperiments(page)
    await experimentRow(page, FIRST_EXPERIMENT).click()
    await clickByText('End Experiment')
    const modal = page
      .locator('.modal-body')
      .filter({ hasText: `after ${FIRST_EXPERIMENT} ends` })
      .last()
    await modal.getByText('Roll out a variant').click()
    const variantSelect = modal.getByRole('combobox', { name: 'Variant' })
    const variantControl = modal
      .locator('.react-select__control')
      .filter({ has: variantSelect })
    await variantControl.scrollIntoViewIfNeeded()
    await variantControl.click()
    await modal
      .getByRole('option')
      .filter({ hasText: 'variant_b' })
      .click()
    await expect(modal).toContainText('100% of users get variant_b')
    await clickByText('Complete experiment')
    await waitForToast()

    log('The results page shows the rollout')
    await expect(page.locator('.experiment-config-rollout')).toContainText(
      'variant_b rolled out to everyone.',
    )
    await visualSnapshot(page, 'experimentation-experiment-completed', testInfo)

    log('The feature serves variant_b to everyone')
    await gotoFeatures()
    await gotoFeature(FEATURE)
    await expect(page.locator(byId('featureVariationWeightb'))).toHaveValue(
      '100',
    )
    await expect(page.locator(byId('featureVariationWeighta'))).toHaveValue('0')
    await click(byId('segment_overrides'))
    await expectNoRolloutOverride(page)
    await closeModal()
  })
})
