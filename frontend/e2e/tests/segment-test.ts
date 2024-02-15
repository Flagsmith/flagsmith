import {
  addSegmentOverride,
  addSegmentOverrideConfig,
  assertTextContent,
  byId,
  click,
  closeModal,
  createFeature,
  createRemoteConfig,
  createSegment,
  createTrait,
  deleteFeature,
  deleteTrait,
  deleteSegment,
  gotoFeature,
  gotoFeatures,
  gotoSegments,
  gotoTraits,
  goToUser,
  log,
  login,
  saveFeatureSegments,
  setSegmentOverrideIndex,
  setText,
  viewFeature,
  waitAndRefresh,
  waitForElementVisible,
  createOrganisationAndProject,
} from '../helpers.cafe';
import { E2E_USER, PASSWORD } from '../config'

export const testSegment1 = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-1')

  log('Create Feature')

  await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])

  log('Segment age rules')
  await gotoSegments()
  // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
  // Rule 1- Age === 18 || Age === 19

  await createSegment(0, '18_or_19', [
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
    // rule 2 >17 or <10
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
  ])

  log('Add segment trait for user')
  await gotoTraits()
  await createTrait(0, 'age', 18)

  await assertTextContent(byId('user-feature-value-0'), '"medium"')
  await gotoFeatures()
  await gotoFeature(0)

  await addSegmentOverride(0, true, 0, [
    { value: 'medium', weight: 0 },
    { value: 'small', weight: 100 },
  ])
  await click('#update-feature-segments-btn')
  await closeModal()
  await waitAndRefresh()

  await gotoTraits()
  await assertTextContent(byId('user-feature-value-0'), '"small"')

  // log('Check user now belongs to segment');
  await assertTextContent(byId('segment-0-name'), '18_or_19')

  // log('Delete segment trait for user');
  await deleteTrait(0)

  log('Set user MV override')
  await click(byId('user-feature-0'))
  await click(byId('select-variation-medium'))
  await click(byId('update-feature-btn'))
  await waitAndRefresh()
  await assertTextContent(byId('user-feature-value-0'), '"medium"')

  log('Delete segment')
  await gotoSegments()
  await deleteSegment(0, '18_or_19')
  await gotoFeatures()
  await deleteFeature(0, 'mv_flag')
}

export const testSegment2 = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-2')

  log('Create segments')
  await gotoSegments()
  await createSegment(0, 'segment_1', [
    {
      name: 'trait',
      operator: 'EQUAL',
      value: '1',
    },
  ])
  await createSegment(1, 'segment_2', [
    {
      name: 'trait2',
      operator: 'EQUAL',
      value: '2',
    },
  ])
  await createSegment(2, 'segment_3', [
    {
      name: 'trait3',
      operator: 'EQUAL',
      value: '3',
    },
  ])

  log('Create Features')
  await gotoFeatures()
  await createFeature(0, 'flag')
  await createRemoteConfig(0, 'config', 0)

  log('Set segment overrides features')
  await viewFeature(0)
  await addSegmentOverrideConfig(0, 3, 2)
  await addSegmentOverrideConfig(1, 2, 1)
  await addSegmentOverrideConfig(2, 1, 0)
  await saveFeatureSegments()
  await viewFeature(1)
  await addSegmentOverride(0, true, 2)
  await addSegmentOverride(1, false, 1)
  await addSegmentOverride(2, true, 0)
  await saveFeatureSegments()

  log('Set user in segment_1')
  await goToUser(0)
  await createTrait(0, 'trait', 1)
  await createTrait(1, 'trait2', 2)
  await createTrait(2, 'trait3', 3)
  // await assertTextContent(byId('segment-0-name'), 'segment_1'); todo: view user segments disabled in edge
  await waitForElementVisible(byId('user-feature-switch-1-on'))
  await assertTextContent(byId('user-feature-value-0'), '1')

  log('Prioritise segment 2')
  await gotoFeatures()
  await gotoFeature(0)
  await setSegmentOverrideIndex(1, 0)
  await saveFeatureSegments()
  await gotoFeature(1)
  await setSegmentOverrideIndex(1, 0)
  await saveFeatureSegments()
  await goToUser(0)
  await waitForElementVisible(byId('user-feature-switch-1-off'))
  await assertTextContent(byId('user-feature-value-0'), '2')

  log('Prioritise segment 3')
  await gotoFeatures()
  await gotoFeature(0)
  await setSegmentOverrideIndex(2, 0)
  await saveFeatureSegments()
  await gotoFeature(1)
  await setSegmentOverrideIndex(2, 0)
  await saveFeatureSegments()
  await goToUser(0)
  await waitForElementVisible(byId('user-feature-switch-1-on'))
  await assertTextContent(byId('user-feature-value-0'), '3')

  log('Clear down features')
  await gotoFeatures()
  await deleteFeature(1, 'flag')
  await deleteFeature(0, 'config')
}

export const testSegment3 = async () => {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-3')

  log('Create features')
  await gotoFeatures()
  await createFeature(0, 'flag', true)
  await createRemoteConfig(0, 'config', 0, 'Description')

  log('Toggle flag for user')
  await goToUser(0)
  await click(byId('user-feature-switch-1-on'))
  await click('#confirm-toggle-feature-btn')
  await waitAndRefresh() // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForElementVisible(byId('user-feature-switch-1-off'))

  log('Edit flag for user')
  await click(byId('user-feature-0'))
  await setText(byId('featureValue'), 'small')
  await click('#update-feature-btn')
  await waitAndRefresh() // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await assertTextContent(byId('user-feature-value-0'), '"small"')

  log('Toggle flag for user again')
  await click(byId('user-feature-switch-1-off'))
  await click('#confirm-toggle-feature-btn')
  await waitAndRefresh() // wait and refresh to avoid issues with data sync from UK -> US in github workflows
  await waitForElementVisible(byId('user-feature-switch-1-on'))
}
