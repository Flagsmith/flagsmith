import {
    addSegmentOverride,
    assertTextContent,
    byId,
    click, closeModal,
    createFeature,
    createRemoteConfig, createSegment, createTrait,
    deleteFeature, deleteSegment, deleteTrait, getText, gotoFeature, gotoFeatures, gotoSegments, gotoTraits,
    log,
    setText, toggleFeature, waitAndRefresh,
    waitForElementVisible,
} from '../helpers.cafe';
import { t } from 'testcafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';

export default async function() {
    log('Create Organisation', 'Initialise Test');
    await click(byId('jsSignup'));
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train'); // visit the url
    await setText(byId('email'), email); // visit the url
    await setText(byId('password'), password); // visit the url
    await click(byId('signup-btn'));
    await setText('[name="orgName"]', 'Bullet Train Ltd');
    await click('#create-org-btn');
    await waitForElementVisible(byId('project-select-page'));

    log('Create Project', 'Initialise Test');
    await click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await click(byId('create-project-btn'));
    await waitForElementVisible((byId('features-page')));

    log('Hide disabled flags', 'Initialise Test');
    await click('#project-settings-link');
    await click(byId('js-sdk-settings'));
    await click(byId('js-hide-disabled-flags'));
    await setText(byId('js-project-name'), 'My Test Project');
    await click(byId('js-confirm'));


    // await click('#features-link');


    log('Create Features', 'Initialise Test');
    await createRemoteConfig(0, 'header_size', 'big');
    await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
        { value: 'medium', weight: 100 },
        { value: 'small', weight: 0 },
    ]);
    await createFeature(1, 'header_enabled', false);

    log('Create Short Life Feature', 'Initialise Test');
    await createFeature(3, 'short_life_feature', false);
    await deleteFeature(3, 'short_life_feature');

    log('Toggle Feature', 'Initialise Test');
    await toggleFeature(0, true);

    log('Try it', 'Initialise Test');
    await t.wait(2000);
    await click('#try-it-btn');
    await t.wait(1500);
    let text = await getText('#try-it-results');
    let json;
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql('big');
    await t.expect(json.mv_flag.value).eql('big');
    await t.expect(json.header_enabled.enabled).eql(true);

    log('Update feature', 'Initialise Test');
    await click(byId('feature-item-1'));
    await setText(byId('featureValue'), '12');
    await click('#update-feature-btn');
    await assertTextContent(byId('feature-value-1'), '12');
    await t.pressKey('esc');
    await closeModal();

    log('Try it again', 'Initialise Test');
    await t.wait(2000);
    await click('#try-it-btn');
    await t.wait(1500);
    text = await getText('#try-it-results');
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql(12);

    log('Change feature value to boolean', 'Initialise Test');
    await click(byId('feature-item-1'));
    await setText(byId('featureValue'), 'false');
    await click('#update-feature-btn');
    await assertTextContent(byId('feature-value-1'), 'false');
    await closeModal();

    log('Try it again 2', 'Initialise Test');
    await t.wait(2000);
    await click('#try-it-btn');
    await t.wait(1500);
    text = await getText('#try-it-results');
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql(false);

    log('Switch environment', 'Initialise Test');
    await click(byId('switch-environment-production'));

    log('Feature should be off under different environment', 'Initialise Test');
    await waitForElementVisible(byId('switch-environment-production-active'));
    await waitForElementVisible(byId('feature-switch-0-off'));

    log('Clear down features', 'Initialise Test');
    await deleteFeature(1, 'header_size');
    await deleteFeature(0, 'header_enabled');

    log('Segment age rules', 'Initialise Test');
    await gotoSegments();
    // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
    // Rule 1- Age === 18 || Age === 19

    await createSegment(0, '18_or_19', [
        // rule 2 =18 || =17
        {
            name: 'age',
            operator: 'EQUAL',
            value: 18,
            ors: [
                {
                    name: 'age',
                    operator: 'EQUAL',
                    value: 17,
                },
            ],
        },
        // rule 2 >17 or <10
        {
            name: 'age',
            operator: 'GREATER_THAN',
            value: 17,
            ors: [
                {
                    name: 'age',
                    operator: 'LESS_THAN',
                    value: 10,
                },
            ],
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


    log('Add segment trait for user', 'Initialise Test');
    await gotoTraits();
    await createTrait(0, 'age', 18);

    await assertTextContent(byId('user-feature-value-0'), '"medium"');
    await gotoFeatures();
    await gotoFeature(0);

    await addSegmentOverride(0, true, 0, [
        { value: 'medium', weight: 0 },
        { value: 'small', weight: 100 },

    ]);
    await click('#update-feature-segments-btn');
    await closeModal();
    await waitAndRefresh();

    await gotoTraits();
    await assertTextContent(byId('user-feature-value-0'), '"small"');

    // log('Check user now belongs to segment');
    await assertTextContent(byId('segment-0-name'), '18_or_19');

    // log('Delete segment trait for user');
    await deleteTrait(0);


    log('Set user MV override', 'Initialise Test');
    await click(byId('user-feature-0'));
    await click(byId('select-variation-medium'));
    await click(byId('update-feature-btn'));
    await waitAndRefresh();
    await assertTextContent(byId('user-feature-value-0'), '"medium"');

    log('Delete segment', 'Initialise Test');
    await gotoSegments();
    await deleteSegment(0, '18_or_19');
    await gotoFeatures();
    await deleteFeature(0, 'mv_flag');
}
