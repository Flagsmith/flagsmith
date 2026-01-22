import { test, expect } from '../test-setup';
import {
  addSegmentOverride,
  addSegmentOverrideConfig,
  assertTextContent,
  assertUserFeatureValue,
  byId,
  clickUserFeature,
  clickUserFeatureSwitch,
  closeModal,
  createFeature,
  createRemoteConfig,
  createSegment,
  createTrait,
  deleteFeature,
  deleteTrait,
  deleteSegment,
  gotoFeature,
  gotoTraits,
  goToUser,
  log,
  saveFeatureSegments,
  setSegmentOverrideIndex,
  waitAndRefresh,
  waitForUserFeatureSwitch,
  cloneSegment,
  setSegmentRule,
  assertInputValue,
  deleteSegmentFromPage,
  createHelpers,
} from '../helpers.playwright';
import { E2E_USER, PASSWORD } from '../config'

// Keep the last rule simple to facilitate update testing
const segmentRules =  [
  // rule 2 =18 || =17
  {
    name: 'age',
    operator: 'EQUAL',
    ors: [
      {
        name: 'age',
        operator: 'EQUAL',
        value: 17,
      },
    ],
    value: 18,
  },
  //rule 2 >17 or <10
  {
    name: 'age',
    operator: 'GREATER_THAN',
    ors: [
      {
        name: 'age',
        operator: 'LESS_THAN',
        value: 10,
      },
    ],
    value: 17,
  },
  // rule 3 !=20
  {
    name: 'age',
    operator: 'NOT_EQUAL',
    value: 20,
  },
  // Rule 4 <= 18
  {
    name: 'age',
    operator: 'LESS_THAN_INCLUSIVE',
    value: 18,
  },
  // Rule 5 >= 18
  {
    name: 'age',
    operator: 'GREATER_THAN_INCLUSIVE',
    value: 18,
  },
]

test('Segment test 1 - Create, update, and manage segments with multivariate flags @oss', async ({ page }) => {
  const helpers = createHelpers(page)

  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-1')
  await helpers.waitForElementVisible(byId('features-page'))

  log('Create Feature')

  await createRemoteConfig(page, 0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])

  await helpers.gotoSegments()

  log('Segment age rules')
  // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
  // Rule 1- Age === 18 || Age === 19

  log('Update segment')
  await helpers.gotoSegments()
  const lastRule = segmentRules[segmentRules.length - 1]
  await createSegment(page, 0, 'segment_to_update', [lastRule])
  await helpers.navigateToSegment('segment_to_update')
  await setSegmentRule(page, 0, 0, lastRule.name, lastRule.operator, lastRule.value + 1)
  await helpers.click(byId('update-segment'))
  log('Check segment rule value')
  await helpers.gotoSegments()
  await helpers.navigateToSegment('segment_to_update')
  await assertInputValue(page, byId(`rule-${0}-value-0`), `${lastRule.value + 1}`)
  await deleteSegmentFromPage(page, 'segment_to_update')

  log('Create segment')
  await createSegment(page, 0, '18_or_19', segmentRules)

  log('Add segment trait for user')
  await gotoTraits(page)
  await createTrait(page, 'age', 18)

  // Wait for trait to be applied and feature values to load
  await waitAndRefresh(page)
  await assertUserFeatureValue(page, 'mv_flag', '"medium"')
  await helpers.gotoFeatures()
  await gotoFeature(page, 'mv_flag')

  await addSegmentOverride(page, 0, true, 0, [
    { value: 'medium', weight: 0 },
    { value: 'small', weight: 100 },
  ])

  await helpers.click('#update-feature-segments-btn')

  // Wait for success message to appear indicating save completed
  await page.waitForSelector('.toast-message', { state: 'visible', timeout: 10000 })

  // Wait for toast to disappear
  await page.waitForSelector('.toast-message', { state: 'hidden', timeout: 10000 })

  await closeModal(page)

  await gotoTraits(page)
  await waitAndRefresh(page)

  await assertUserFeatureValue(page, 'mv_flag', '"small"')

  // log('Check user now belongs to segment');
  const segmentElement = page.locator('[data-test^="segment-"][data-test$="-name"]').filter({ hasText: '18_or_19' });
  await expect(segmentElement).toBeVisible()

  // log('Delete segment trait for user');
  await deleteTrait(page, 'age')

  log('Set user MV override')
  await clickUserFeature(page, 'mv_flag')
  await helpers.click(byId('select-variation-medium'))
  await helpers.click(byId('update-feature-btn'))
  await waitAndRefresh(page)
  await assertUserFeatureValue(page, 'mv_flag', '"medium"')

  log('Clone segment')
  await helpers.gotoSegments()
  await cloneSegment(page, 0, '0cloned-segment')
  await deleteSegment(page, 0, '0cloned-segment')

  log('Delete segment')
  await helpers.gotoSegments()
  await deleteSegment(page, 0, '18_or_19')
  await helpers.gotoFeatures()
  await deleteFeature(page, 'mv_flag')
})

test('Segment test 2 - Test segment priority and overrides @oss', async ({ page }) => {
  const helpers = createHelpers(page)

  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-2')
  await helpers.waitForElementVisible(byId('features-page'))

  log('Create segments')
  await helpers.gotoSegments()
  await createSegment(page, 0, 'segment_1', [
    {
      name: 'trait',
      operator: 'EQUAL',
      value: '1',
    },
  ])
  await createSegment(page, 1, 'segment_2', [
    {
      name: 'trait2',
      operator: 'EQUAL',
      value: '2',
    },
  ])
  await createSegment(page, 2, 'segment_3', [
    {
      name: 'trait3',
      operator: 'EQUAL',
      value: '3',
    },
  ])

  log('Create Features')
  await helpers.gotoFeatures()
  await createFeature(page, 0, 'flag')
  await createRemoteConfig(page, 0, 'config', 0)

  log('Set segment overrides features')
  await gotoFeature(page, 'config')
  await addSegmentOverrideConfig(page, 0, 1, 0)
  await addSegmentOverrideConfig(page, 1, 2, 0)
  await addSegmentOverrideConfig(page, 2, 3, 0)
  await saveFeatureSegments(page)
  await gotoFeature(page, 'flag')
  await addSegmentOverride(page, 0, true, 0)
  await addSegmentOverride(page, 1, false, 0)
  await addSegmentOverride(page, 2, true, 0)
  await saveFeatureSegments(page)

  log('Set user in segment_1')
  await goToUser(page, 0)
  await createTrait(page, 'trait', 1)
  await createTrait(page, 'trait2', 2)
  await createTrait(page, 'trait3', 3)
  // await assertTextContent(page, byId('segment-0-name'), 'segment_1'); todo: view user segments disabled in edge
  await waitForUserFeatureSwitch(page, 'flag', 'on')
  // Wait for feature values to update after trait creation
  await page.waitForTimeout(1000)
  await assertUserFeatureValue(page, 'config', '1')

  log('Prioritise segment 2')
  await helpers.gotoFeatures()
  await gotoFeature(page, 'config')
  await setSegmentOverrideIndex(page, 1, 0)
  await saveFeatureSegments(page)
  await gotoFeature(page, 'flag')
  await setSegmentOverrideIndex(page, 1, 0)
  await saveFeatureSegments(page)
  await goToUser(page, 0)
  await waitForUserFeatureSwitch(page, 'flag', 'off')
  await assertUserFeatureValue(page, 'config', '2')

  log('Prioritise segment 3')
  await helpers.gotoFeatures()
  await gotoFeature(page, 'config')
  await setSegmentOverrideIndex(page, 2, 0)
  await saveFeatureSegments(page)
  await gotoFeature(page, 'flag')
  await setSegmentOverrideIndex(page, 2, 0)
  await saveFeatureSegments(page)
  await goToUser(page, 0)
  await waitForUserFeatureSwitch(page, 'flag', 'on')
  await assertUserFeatureValue(page, 'config', '3')

  log('Clear down features')
  await helpers.gotoFeatures()
  await deleteFeature(page, 'flag')
  await deleteFeature(page, 'config')
})

test('Segment test 3 - Test user-specific feature overrides @oss', async ({ page }) => {
  const helpers = createHelpers(page)

  log('Login')
  await helpers.login(E2E_USER, PASSWORD)
  await helpers.click('#project-select-3')
  await helpers.waitForElementVisible(byId('features-page'))

  log('Create features')
  await helpers.gotoFeatures()
  await createFeature(page, 0, 'flag', true)
  await createRemoteConfig(page, 0, 'config', 0, 'Description')

  log('Toggle flag for user')
  await goToUser(page, 0)
  await clickUserFeatureSwitch(page, 'flag', 'on')
  await helpers.click('#confirm-toggle-feature-btn')
  await waitAndRefresh(page) // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForUserFeatureSwitch(page, 'flag', 'off')

  log('Edit flag for user')
  await clickUserFeature(page, 'config')
  await helpers.setText(byId('featureValue'), 'small')
  await helpers.click('#update-feature-btn')
  await waitAndRefresh(page) // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await assertUserFeatureValue(page, 'config', '"small"')

  log('Toggle flag for user again')
  await clickUserFeatureSwitch(page, 'flag', 'off');
  await helpers.click('#confirm-toggle-feature-btn');
  await waitAndRefresh(page); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForUserFeatureSwitch(page, 'flag', 'on');
})
