import { test, expect } from '../test-setup';
import { byId, log, createHelpers, visualSnapshot, getFlagsmith } from '../helpers';
import { E2E_USER, PASSWORD, E2E_TEST_IDENTITY, E2E_SEGMENT_PROJECT_1, E2E_SEGMENT_PROJECT_2, E2E_SEGMENT_PROJECT_3 } from '../config'

const REMOTE_CONFIG_FEATURE = 'remote_config'
const FLAG_FEATURE = 'flag'

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

// (age_any = 18 AND team = "alpha") OR (age_any = 25 AND team = "beta")
// Note: `ors` field is reused for "additional conditions in the same group" — in ANY mode these are AND-ed.
const segmentAnyRules = [
  {
    name: 'age_any',
    operator: 'EQUAL',
    value: 18,
    ors: [
      {
        name: 'team',
        operator: 'EQUAL',
        value: 'alpha',
      },
    ],
  },
  {
    name: 'age_any',
    operator: 'EQUAL',
    value: 25,
    ors: [
      {
        name: 'team',
        operator: 'EQUAL',
        value: 'beta',
      },
    ],
  },
]

test('Segment test 1 - Create, update, and manage segments with multivariate flags @oss', async ({ page }, testInfo) => {
  const {
    addSegmentOverride,
    assertInputValue,
    assertUserFeatureValue,
    click,
    clickUserFeature,
    cloneSegment,
    closeModal,
    createRemoteConfig,
    createSegment,
    createTrait,
    deleteFeature,
    deleteSegment,
    deleteSegmentFromPage,
    deleteTrait,
    gotoFeature,
    gotoFeatures,
    gotoProject,
    gotoSegments,
    gotoTraits,
    login,
    navigateToSegment,
    setSegmentRule,
    waitAndRefresh,
    waitForElementVisible,
    waitForToast,
    waitForToastsToClear,
  } = createHelpers(page)

  log('Login')
  await login(E2E_USER, PASSWORD)
  await gotoProject(E2E_SEGMENT_PROJECT_1)
  await waitForElementVisible(byId('features-page'))

  log('Create Feature')

  await createRemoteConfig({ name: 'mv_flag', value: 'big', mvs: [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ]})

  await gotoSegments()

  log('Segment age rules')
  // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
  // Rule 1- Age === 18 || Age === 19

  log('Update segment')
  await gotoSegments()
  const lastRule = segmentRules[segmentRules.length - 1]
  await createSegment('segment_to_update', [lastRule])
  await navigateToSegment('segment_to_update')
  await setSegmentRule(0, 0, lastRule.name, lastRule.operator, lastRule.value + 1)
  await click(byId('update-segment'))
  log('Check segment rule value')
  await gotoSegments()
  await navigateToSegment('segment_to_update')
  await assertInputValue(byId(`rule-${0}-value-0`), `${lastRule.value + 1}`)
  await deleteSegmentFromPage('segment_to_update')

  await waitForToastsToClear()
  await visualSnapshot(page, 'segments-list', testInfo)

  log('Create segment')
  await createSegment('18_or_19', segmentRules)

  log('Add segment trait for user')
  await gotoTraits(E2E_TEST_IDENTITY)
  await visualSnapshot(page, 'identity-traits', testInfo)

  await createTrait('age', 18)

  // Wait for trait to be applied and feature values to load
  await waitAndRefresh()
  await assertUserFeatureValue('mv_flag', '"medium"')
  await gotoFeatures()
  await gotoFeature('mv_flag')

  await addSegmentOverride(0, true, 0, [
    { value: 'medium', weight: 0 },
    { value: 'small', weight: 100 },
  ])

  await waitForToastsToClear()
  await click('#update-feature-segments-btn')
  await waitForToast()
  await closeModal()

  await gotoTraits(E2E_TEST_IDENTITY)
  await waitAndRefresh()

  await assertUserFeatureValue('mv_flag', '"small"')

  // log('Check user now belongs to segment');
  const segmentElement = page.locator('[data-test^="segment-"][data-test$="-name"]').filter({ hasText: '18_or_19' });
  await expect(segmentElement).toBeVisible()

  // log('Delete segment trait for user');
  await deleteTrait('age')

  log('Set user MV override')
  await clickUserFeature('mv_flag')
  await click(byId('select-variation-medium'))
  await click(byId('update-feature-btn'))
  await waitAndRefresh()
  await assertUserFeatureValue('mv_flag', '"medium"')

  log('Clone segment')
  await gotoSegments()
  await cloneSegment('18_or_19', '0cloned-segment')
  await deleteSegment('0cloned-segment')

  log('Delete segment')
  await gotoSegments()
  await deleteSegment('18_or_19')
  await gotoFeatures()
  await deleteFeature('mv_flag')
})

test('Segment test 2 - Test segment priority and overrides @oss', async ({ page }) => {
  const {
    addSegmentOverride,
    addSegmentOverrideConfig,
    assertUserFeatureValue,
    createFeature,
    createRemoteConfig,
    createSegment,
    createTrait,
    deleteFeature,
    gotoFeature,
    gotoFeatures,
    gotoProject,
    gotoSegments,
    goToUser,
    login,
    saveFeatureSegments,
    setSegmentOverrideIndex,
    waitForElementVisible,
    waitForUserFeatureSwitch,
  } = createHelpers(page)

  log('Login')
  await login(E2E_USER, PASSWORD)
  await gotoProject(E2E_SEGMENT_PROJECT_2)
  await waitForElementVisible(byId('features-page'))

  log('Create segments')
  await gotoSegments()
  await createSegment('segment_1', [
    {
      name: 'trait',
      operator: 'EQUAL',
      value: '1',
    },
  ])
  await createSegment('segment_2', [
    {
      name: 'trait2',
      operator: 'EQUAL',
      value: '2',
    },
  ])
  await createSegment('segment_3', [
    {
      name: 'trait3',
      operator: 'EQUAL',
      value: '3',
    },
  ])

  log('Create Features')
  await gotoFeatures()
  await createFeature({ name: 'flag' })
  await createRemoteConfig({ name: 'config', value: 0 })

  log('Set segment overrides features')
  await gotoFeature('config')
  await addSegmentOverrideConfig(0, 1, 0)
  await addSegmentOverrideConfig(1, 2, 0)
  await addSegmentOverrideConfig(2, 3, 0)
  await saveFeatureSegments()
  await gotoFeature('flag')
  await addSegmentOverride(0, true, 0)
  await addSegmentOverride(1, false, 0)
  await addSegmentOverride(2, true, 0)
  await saveFeatureSegments()

  log('Set user in segment_1')
  await goToUser(E2E_TEST_IDENTITY)
  await createTrait('trait', 1)
  await createTrait('trait2', 2)
  await createTrait('trait3', 3)
  await waitForUserFeatureSwitch('flag', 'on')
  // Wait for feature values to update after trait creation
  await page.waitForTimeout(1000)
  await assertUserFeatureValue('config', '1')

  log('Prioritise segment 2')
  await gotoFeatures()
  await gotoFeature('config')
  await setSegmentOverrideIndex(1, 0)
  await saveFeatureSegments()
  await gotoFeature('flag')
  await setSegmentOverrideIndex(1, 0)
  await saveFeatureSegments()
  await goToUser(E2E_TEST_IDENTITY)
  await waitForUserFeatureSwitch('flag', 'off')
  await assertUserFeatureValue('config', '2')

  log('Prioritise segment 3')
  await gotoFeatures()
  await gotoFeature('config')
  await setSegmentOverrideIndex(2, 0)
  await saveFeatureSegments()
  await gotoFeature('flag')
  await setSegmentOverrideIndex(2, 0)
  await saveFeatureSegments()
  await goToUser(E2E_TEST_IDENTITY)
  await waitForUserFeatureSwitch('flag', 'on')
  await assertUserFeatureValue('config', '3')

  log('Clear down features')
  await gotoFeatures()
  await deleteFeature('flag')
  await deleteFeature('config')
})

test('Segment test 3 - Test user-specific feature overrides @oss', async ({ page }, testInfo) => {
  const {
    assertUserFeatureValue,
    click,
    clickUserFeature,
    clickUserFeatureSwitch,
    closeModal,
    createFeature,
    createRemoteConfig,
    deleteFeature,
    gotoFeature,
    gotoFeatures,
    gotoProject,
    goToUser,
    login,
    setText,
    waitAndRefresh,
    waitForElementVisible,
    waitForUserFeatureSwitch,
  } = createHelpers(page)

  log('Login')
  await login(E2E_USER, PASSWORD)
  await gotoProject(E2E_SEGMENT_PROJECT_3)
  await waitForElementVisible(byId('features-page'))

  log('Create features')
  await gotoFeatures()
  await createFeature({ name: FLAG_FEATURE, value: true })
  await createRemoteConfig({ name: REMOTE_CONFIG_FEATURE, value: 0, description: 'Description' })

  log('Toggle flag for user')
  await goToUser(E2E_TEST_IDENTITY)
  await clickUserFeatureSwitch(FLAG_FEATURE, 'on')
  await click('#confirm-toggle-feature-btn')
  await waitAndRefresh() // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForUserFeatureSwitch(FLAG_FEATURE, 'off')

  log('Edit flag for user')
  await clickUserFeature(REMOTE_CONFIG_FEATURE)
  await setText(byId('featureValue'), 'small')
  await click('#update-feature-btn')
  await waitAndRefresh() // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await assertUserFeatureValue(REMOTE_CONFIG_FEATURE, '"small"')

  log('Verify identity override appears in feature modal')
  await gotoFeatures()
  await gotoFeature(REMOTE_CONFIG_FEATURE)
  await click('[data-test="identity_overrides"]')
  await page.waitForTimeout(1000) // Wait for identity overrides to load

  // Check that the test identity appears in the list
  const identityRow = page.locator('[id="users-list"]').locator('.list-item').filter({
    hasText: E2E_TEST_IDENTITY
  })
  await expect(identityRow).toBeVisible()

  // Check that the override value is displayed correctly
  const valueInList = identityRow.locator('.table-column').filter({ hasText: 'small' })
  await expect(valueInList).toBeVisible()

  await visualSnapshot(page, 'feature-identity-overrides', testInfo)

  log('Close modal')
  await closeModal()

  log('Toggle flag for user again')
  await goToUser(E2E_TEST_IDENTITY)
  await clickUserFeatureSwitch(FLAG_FEATURE, 'off');
  await click('#confirm-toggle-feature-btn');
  await waitAndRefresh(); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForUserFeatureSwitch(FLAG_FEATURE, 'on');

  log('Clear down features')
  await gotoFeatures()
  await deleteFeature(FLAG_FEATURE)
  await deleteFeature(REMOTE_CONFIG_FEATURE)
})

test('Segment test 4 - Create ANY rule type segment and verify match changes when rule is updated @oss', async ({ page }) => {
  const ANY_FEATURE = 'any_segment_feature'
  const ANY_SEGMENT = 'any_segment_test'
  const {
    addSegmentOverrideConfig,
    assertUserFeatureValue,
    click,
    createRemoteConfig,
    createSegment,
    createTrait,
    deleteFeature,
    deleteSegment,
    deleteTrait,
    goToUser,
    gotoFeature,
    gotoFeatures,
    gotoProject,
    gotoSegments,
    gotoTraits,
    login,
    navigateToSegment,
    saveFeatureSegments,
    setSegmentRule,
    waitAndRefresh,
    waitForElementVisible,
  } = createHelpers(page)
  const flagsmith = await getFlagsmith()
  const hasFeature = flagsmith.hasFeature('segment_any_rule_type')

  log('Login')
  await login(E2E_USER, PASSWORD)

  if (!hasFeature) {
    log('Skipping ANY segment test, feature not enabled.')
    test.skip()
    return
  }

  await gotoProject(E2E_SEGMENT_PROJECT_1)
  await waitForElementVisible(byId('features-page'))

  log('Create remote config feature with default value')
  await createRemoteConfig({ name: ANY_FEATURE, value: 'default' })

  log('Set traits matching the first ANY group')
  await gotoTraits(E2E_TEST_IDENTITY)
  await createTrait('age_any', 18)
  await createTrait('team', 'alpha')

  log('Create ANY-mode segment')
  await gotoSegments()
  await createSegment(ANY_SEGMENT, segmentAnyRules, 'ANY')

  log('Override feature value via segment')
  await gotoFeatures()
  await gotoFeature(ANY_FEATURE)
  await addSegmentOverrideConfig(0, 'overridden', 0)
  await saveFeatureSegments()

  log('Verify user is in the segment (gets overridden value)')
  await goToUser(E2E_TEST_IDENTITY)
  await waitAndRefresh()
  await assertUserFeatureValue(ANY_FEATURE, '"overridden"')

  log('Update segment so user no longer matches')
  await gotoSegments()
  await navigateToSegment(ANY_SEGMENT)
  // Change the first group's `team` condition from "alpha" to "gamma" — user has team=alpha so no longer matches.
  await setSegmentRule(0, 1, 'team', 'EQUAL', 'gamma')
  await click(byId('update-segment'))

  log('Verify user is no longer in the segment (gets default value)')
  await goToUser(E2E_TEST_IDENTITY)
  await waitAndRefresh()
  await assertUserFeatureValue(ANY_FEATURE, '"default"')

  log('Clean up feature, segment, and traits')
  await gotoFeatures()
  await deleteFeature(ANY_FEATURE)
  await gotoSegments()
  await deleteSegment(ANY_SEGMENT)
  await gotoTraits(E2E_TEST_IDENTITY)
  await deleteTrait('age_any')
  await deleteTrait('team')
})
