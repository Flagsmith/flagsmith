import { test } from '@playwright/test';
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
} from '../helpers/helpers';
import { E2E_USER, PASSWORD } from '../config';

test('@oss Segment test 1 - Age rules and overrides', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-1');

  log('Create Feature');
  await createRemoteConfig(page, 0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ]);

  log('Segment age rules');
  await gotoSegments(page);
  // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
  // Rule 1- Age === 18 || Age === 19

  await createSegment(page, 0, '18_or_19', [
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
  ]);

  log('Add segment trait for user');
  await gotoTraits(page);
  await createTrait(page, 0, 'age', 18);

  await assertTextContent(page, byId('user-feature-value-0'), '"medium"');
  await gotoFeatures(page);
  await gotoFeature(page, 0);

  await addSegmentOverride(page, 0, true, 0, [
    { value: 'medium', weight: 0 },
    { value: 'small', weight: 100 },
  ]);
  await click(page, '#update-feature-segments-btn');
  await closeModal(page);
  await waitAndRefresh(page);

  await gotoTraits(page);
  await assertTextContent(page, byId('user-feature-value-0'), '"small"');

  await assertTextContent(page, byId('segment-0-name'), '18_or_19');

  await deleteTrait(page, 0);

  log('Set user MV override');
  await click(page, byId('user-feature-0'));
  await click(page, byId('select-variation-medium'));
  await click(page, byId('update-feature-btn'));
  await waitAndRefresh(page);
  await assertTextContent(page, byId('user-feature-value-0'), '"medium"');

  log('Delete segment');
  await gotoSegments(page);
  await deleteSegment(page, 0, '18_or_19');
  await gotoFeatures(page);
  await deleteFeature(page, 0, 'mv_flag');
});

test('@oss Segment test 2 - Multiple segments and prioritization', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-2');

  log('Create segments');
  await gotoSegments(page);
  await createSegment(page, 0, 'segment_1', [
    {
      name: 'trait',
      operator: 'EQUAL',
      value: '1',
    },
  ]);
  await createSegment(page, 1, 'segment_2', [
    {
      name: 'trait2',
      operator: 'EQUAL',
      value: '2',
    },
  ]);
  await createSegment(page, 2, 'segment_3', [
    {
      name: 'trait3',
      operator: 'EQUAL',
      value: '3',
    },
  ]);

  log('Create Features');
  await gotoFeatures(page);
  await createFeature(page, 0, 'flag');
  await createRemoteConfig(page, 0, 'config', 0);

  log('Set segment overrides features');
  await viewFeature(page, 0);
  await addSegmentOverrideConfig(page, 0, 1, 0);
  await addSegmentOverrideConfig(page, 1, 2, 0);
  await addSegmentOverrideConfig(page, 2, 3, 0);
  await saveFeatureSegments(page);
  await viewFeature(page, 1);
  await addSegmentOverride(page, 0, true, 0);
  await addSegmentOverride(page, 1, false, 0);
  await addSegmentOverride(page, 2, true, 0);
  await saveFeatureSegments(page);

  log('Set user in segment_1');
  await goToUser(page, 0);
  await createTrait(page, 0, 'trait', 1);
  await createTrait(page, 1, 'trait2', 2);
  await createTrait(page, 2, 'trait3', 3);
  await waitForElementVisible(page, byId('user-feature-switch-1-on'));
  await assertTextContent(page, byId('user-feature-value-0'), '1');

  log('Prioritise segment 2');
  await gotoFeatures(page);
  await gotoFeature(page, 0);
  await setSegmentOverrideIndex(page, 1, 0);
  await saveFeatureSegments(page);
  await gotoFeature(page, 1);
  await setSegmentOverrideIndex(page, 1, 0);
  await saveFeatureSegments(page);
  await goToUser(page, 0);
  await waitForElementVisible(page, byId('user-feature-switch-1-off'));
  await assertTextContent(page, byId('user-feature-value-0'), '2');

  log('Prioritise segment 3');
  await gotoFeatures(page);
  await gotoFeature(page, 0);
  await setSegmentOverrideIndex(page, 2, 0);
  await saveFeatureSegments(page);
  await gotoFeature(page, 1);
  await setSegmentOverrideIndex(page, 2, 0);
  await saveFeatureSegments(page);
  await goToUser(page, 0);
  await waitForElementVisible(page, byId('user-feature-switch-1-on'));
  await assertTextContent(page, byId('user-feature-value-0'), '3');

  log('Clear down features');
  await gotoFeatures(page);
  await deleteFeature(page, 1, 'flag');
  await deleteFeature(page, 0, 'config');
});

test('@oss Segment test 3 - User feature toggles', async ({ page }) => {
  log('Login');
  await login(page, E2E_USER, PASSWORD);
  await click(page, '#project-select-3');

  log('Create features');
  await gotoFeatures(page);
  await createFeature(page, 0, 'flag', true);
  await createRemoteConfig(page, 0, 'config', 0, 'Description');

  log('Toggle flag for user');
  await goToUser(page, 0);
  await click(page, byId('user-feature-switch-1-on'));
  await click(page, '#confirm-toggle-feature-btn');
  await waitAndRefresh(page);
  await waitForElementVisible(page, byId('user-feature-switch-1-off'));

  log('Edit flag for user');
  await click(page, byId('user-feature-0'));
  await setText(page, byId('featureValue'), 'small');
  await click(page, '#update-feature-btn');
  await waitAndRefresh(page);
  await assertTextContent(page, byId('user-feature-value-0'), '"small"');

  log('Toggle flag for user again');
  await click(page, byId('user-feature-switch-1-off'));
  await click(page, '#confirm-toggle-feature-btn');
  await waitAndRefresh(page);
  await waitForElementVisible(page, byId('user-feature-switch-1-on'));
});
