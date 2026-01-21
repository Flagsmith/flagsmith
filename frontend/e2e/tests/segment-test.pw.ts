import { test, expect } from '../test-setup';
import {
  addSegmentOverride,
  addSegmentOverrideConfig,
  assertTextContent,
  byId,
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
  viewFeature,
  waitAndRefresh,
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
  await helpers.click(byId('segment-0-name'))
  await setSegmentRule(page, 0, 0, lastRule.name, lastRule.operator, lastRule.value + 1)
  await helpers.click(byId('update-segment'))
  log('Check segment rule value')
  await helpers.gotoSegments()
  await helpers.click(byId('segment-0-name'))
  await assertInputValue(page, byId(`rule-${0}-value-0`), `${lastRule.value + 1}`)
  await deleteSegmentFromPage(page, 'segment_to_update')

  log('Create segment')
  await createSegment(page, 0, '18_or_19', segmentRules)


  log('Add segment trait for user')
  await gotoTraits(page)
  await createTrait(page, 0, 'age', 18)

  await assertTextContent(page, byId('user-feature-value-0'), '"medium"')
  await helpers.gotoFeatures()
  await gotoFeature(page, 0)

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

  await assertTextContent(page, byId('user-feature-value-0'), '"small"')

  // log('Check user now belongs to segment');
  await assertTextContent(page, byId('segment-0-name'), '18_or_19')

  // log('Delete segment trait for user');
  await deleteTrait(page, 0)

  log('Set user MV override')
  await helpers.click(byId('user-feature-0'))
  await helpers.click(byId('select-variation-medium'))
  await helpers.click(byId('update-feature-btn'))
  await waitAndRefresh(page)
  await assertTextContent(page, byId('user-feature-value-0'), '"medium"')

  log('Clone segment')
  await helpers.gotoSegments()
  await cloneSegment(page, 0, '0cloned-segment')
  await deleteSegment(page, 0, '0cloned-segment')

  log('Delete segment')
  await helpers.gotoSegments()
  await deleteSegment(page, 0, '18_or_19')
  await helpers.gotoFeatures()
  await deleteFeature(page, 0, 'mv_flag')
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
  await viewFeature(page, 0)
  await addSegmentOverrideConfig(page, 0, 1, 0)
  await addSegmentOverrideConfig(page, 1, 2, 0)
  await addSegmentOverrideConfig(page, 2, 3, 0)
  await saveFeatureSegments(page)
  await viewFeature(page, 1)
  await addSegmentOverride(page, 0, true, 0)
  await addSegmentOverride(page, 1, false, 0)
  await addSegmentOverride(page, 2, true, 0)
  await saveFeatureSegments(page)

  log('Set user in segment_1')
  await goToUser(page, 0)
  await createTrait(page, 0, 'trait', 1)
  await createTrait(page, 1, 'trait2', 2)
  await createTrait(page, 2, 'trait3', 3)
  // await assertTextContent(page, byId('segment-0-name'), 'segment_1'); todo: view user segments disabled in edge
  await helpers.waitForElementVisible(byId('user-feature-switch-1-on'))
  await assertTextContent(page, byId('user-feature-value-0'), '1')

  log('Prioritise segment 2')
  await helpers.gotoFeatures()
  await gotoFeature(page, 0)
  await setSegmentOverrideIndex(page, 1, 0)
  await saveFeatureSegments(page)
  await gotoFeature(page, 1)
  await setSegmentOverrideIndex(page, 1, 0)
  await saveFeatureSegments(page)
  await goToUser(page, 0)
  await helpers.waitForElementVisible(byId('user-feature-switch-1-off'))
  await assertTextContent(page, byId('user-feature-value-0'), '2')

  log('Prioritise segment 3')
  await helpers.gotoFeatures()
  await gotoFeature(page, 0)
  await setSegmentOverrideIndex(page, 2, 0)
  await saveFeatureSegments(page)
  await gotoFeature(page, 1)
  await setSegmentOverrideIndex(page, 2, 0)
  await saveFeatureSegments(page)
  await goToUser(page, 0)
  await helpers.waitForElementVisible(byId('user-feature-switch-1-on'))
  await assertTextContent(page, byId('user-feature-value-0'), '3')

  log('Clear down features')
  await helpers.gotoFeatures()
  await deleteFeature(page, 1, 'flag')
  await deleteFeature(page, 0, 'config')
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
  await helpers.click(byId('user-feature-switch-1-on'))
  await helpers.click('#confirm-toggle-feature-btn')
  await waitAndRefresh(page) // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await helpers.waitForElementVisible(byId('user-feature-switch-1-off'))

  log('Edit flag for user')
  await helpers.click(byId('user-feature-0'))
  await helpers.setText(byId('featureValue'), 'small')
  await helpers.click('#update-feature-btn')
  await waitAndRefresh(page) // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await assertTextContent(page, byId('user-feature-value-0'), '"small"')

  log('Toggle flag for user again')
  await helpers.click(byId('user-feature-switch-1-off'));
  await helpers.click('#confirm-toggle-feature-btn');
  await waitAndRefresh(page); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await helpers.waitForElementVisible(byId('user-feature-switch-1-on'));
})