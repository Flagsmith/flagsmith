import {test, expect} from '@playwright/test';
import {
    addSegmentOverride,
    addSegmentOverrideConfig, assertTextContent,
    byId,
    click, createFeature, createRemoteConfig,
    createSegment, createTrait, deleteFeature, gotoFeature,
    gotoFeatures,
    gotoSegments, goToUser,
    log,
    login, saveFeatureSegments, setSegmentOverrideIndex,
    setText, viewFeature, waitAndRefresh,
    waitForElementVisible
} from "./helpers.e2e";
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;

test('Segments', async ({page}) => {
    await page.goto(url);
    await login(email, password,page);
    await click('#project-select-0',page);

    log('Create segments', 'Segment Test');
    await gotoSegments(page);
    await createSegment(page,0, 'segment_1', [
        {
            name: 'trait',
            operator: 'EQUAL',
            value: '1',
        },
    ]);
    await createSegment(page,1, 'segment_2', [
        {
            name: 'trait2',
            operator: 'EQUAL',
            value: '2',
        },
    ]);
    await createSegment(page,2, 'segment_3', [
        {
            name: 'trait3',
            operator: 'EQUAL',
            value: '3',
        },
    ]);

    log('Create Features');
    await gotoFeatures(page);
    await createFeature(page,0, 'flag');
    await createRemoteConfig(page,0, 'config', 0);

    log('Set segment overrides features');
    await viewFeature(0,page);
    await addSegmentOverrideConfig(page,0, 3, 2);
    await addSegmentOverrideConfig(page,1, 2, 1);
    await addSegmentOverrideConfig(page,2, 1, 0);
    await saveFeatureSegments(page);
    await viewFeature(1,page);
    await addSegmentOverride(page,0, true, 2);
    await addSegmentOverride(page,1, false, 1);
    await addSegmentOverride(page,2, true, 0);
    await saveFeatureSegments(page);

    log('Set user in segment_1', 'Segment Test');
    await goToUser(0,page);
    await createTrait(0, 'trait', 1,page);
    await createTrait(1, 'trait2', 2,page);
    await createTrait(2, 'trait3', 3,page);
    // await assertTextContent(byId('segment-0-name'), 'segment_1'); todo: view user segments disabled in edge
    await waitForElementVisible(byId('user-feature-switch-1-on'),page);
    await assertTextContent(byId('user-feature-value-0'), '1',page);

    log('Prioritise segment 2', 'Segment Test');
    await gotoFeatures(page);
    await gotoFeature(0,page);
    await setSegmentOverrideIndex(1, 0,page);
    await saveFeatureSegments(page);
    await gotoFeature(1,page);
    await setSegmentOverrideIndex(1, 0,page);
    await saveFeatureSegments(page);
    await goToUser(0,page);
    await waitForElementVisible(byId('user-feature-switch-1-off'),page);
    await assertTextContent(byId('user-feature-value-0'), '2',page);

    log('Prioritise segment 3', 'Segment Test');
    await gotoFeatures(page);
    await gotoFeature(0,page);
    await setSegmentOverrideIndex(2, 0,page);
    await saveFeatureSegments(page);
    await gotoFeature(1,page);
    await setSegmentOverrideIndex(2, 0,page);
    await saveFeatureSegments(page);
    await goToUser(0,page);
    await waitForElementVisible(byId('user-feature-switch-1-on'),page);
    await assertTextContent(byId('user-feature-value-0'), '3',page);
    log('Clear down features', 'Segment Test');
    await gotoFeatures(page);
    await deleteFeature(page,1, 'flag');
    await deleteFeature(page,0, 'config');

    log('Create features', 'Segment Test');
    await createFeature(page,0, 'flag', true);
    await createRemoteConfig(page,0, 'config', 0, 'Description');

    log('Toggle flag for user', 'Segment Test');
    await goToUser(0,page);
    await click(byId('user-feature-switch-1-on'),page);
    await click('#confirm-toggle-feature-btn',page);
    await waitAndRefresh(page); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
    await waitForElementVisible(byId('user-feature-switch-1-off'),page);

    log('Edit flag for user', 'Segment Test');
    await click(byId('user-feature-0'),page);
    await setText(byId('featureValue'), 'small',page);
    await click('#update-feature-btn',page);
    await waitAndRefresh(page); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
    await assertTextContent(byId('user-feature-value-0'), '"small"',page);

    log('Toggle flag for user again', 'Segment Test');
    await click(byId('user-feature-switch-1-off'),page);
    await click('#confirm-toggle-feature-btn',page);
    await waitAndRefresh(page); // wait and refresh to avoid issues with data sync from UK -> US in github workflows
    await waitForElementVisible(byId('user-feature-switch-1-on'),page);
});
