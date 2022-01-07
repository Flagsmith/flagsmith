import { t } from 'testcafe';
import fetch from 'node-fetch';
import Project from '../common/project';
import {
    assertTextContent,
    byId, click,
    createFeature,
    createRemoteConfig, createSegment, createTrait,
    deleteFeature, deleteSegment, deleteTrait, getText, gotoSegments, gotoTraits, log,
    setText,
    toggleFeature,
    waitForElementVisible,
} from './helpers.cafe';

require('dotenv').config();

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;

fixture`Initialise`
    .before(async () => {
        let token;
        if (process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`]) {
            token = process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];
        }

        if (token) {
            await fetch(`${Project.api}e2etests/teardown/`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-E2E-Test-Auth-Token': token.trim(),
                },
                body: JSON.stringify({}),
            }).then((res) => {
                if (res.ok) {
                    // eslint-disable-next-line no-console
                    console.log('\n', '\x1b[32m', 'e2e teardown successful', '\x1b[0m', '\n');
                } else {
                    // eslint-disable-next-line no-console
                    console.error('\n', '\x1b[31m', 'e2e teardown failed', res.status, '\x1b[0m', '\n');
                }
            });
        } else {
            // eslint-disable-next-line no-console
            console.error('\n', '\x1b[31m', 'e2e teardown failed - no available token', '\x1b[0m', '\n');
        }
    })
    .page`${url}`;


test('[Initialise]', async () => {
    log('Create Organisation');
    await click(byId("jsSignup"))
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train'); // visit the url
    await setText(byId('email'), email); // visit the url
    await setText(byId('password'), password); // visit the url
    await click(byId('signup-btn'));
    await setText('[name="orgName"]', 'Bullet Train Ltd');
    await click('#create-org-btn');
    await waitForElementVisible(byId('project-select-page'));

    log('Create Project');
    await click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await click(byId('create-project-btn'));
    await waitForElementVisible((byId('features-page')));

    log('Create Features');
    await createRemoteConfig(0, 'header_size', 'big');
    await createFeature(1, 'header_enabled', false);

    log('Create Short Life Feature');
    await createFeature(2, 'short_life_feature', false);
    await deleteFeature(2, 'short_life_feature');

    log('Toggle Feature');
    await toggleFeature(0, true);

    log('Try it');
    await click('#try-it-btn');
    let text = await getText('#try-it-results');
    let json;
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql('big');
    await t.expect(json.header_enabled.enabled).eql(true);

    log('Update feature');
    await click(byId('feature-item-1'));
    await setText(byId('featureValue'), '12');
    await click('#update-feature-btn');
    await assertTextContent(byId('feature-value-1'), '12');

    log('Try it again');
    await click('#try-it-btn');
    text = await getText('#try-it-results');
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql(12);

    log('Change feature value to boolean');
    await click(byId('feature-item-1'));
    await setText(byId('featureValue'), 'false');
    await setText(byId('featureValue'), 'false');
    await click('#update-feature-btn');
    await assertTextContent(byId('feature-value-1'), 'false');

    log('Change feature value to boolean');
    await click('#try-it-btn');
    text = await getText('#try-it-results');
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql(false);

    log('Switch environment');
    await click(byId('switch-environment-production'));

    log('Feature should be off under different environment');
    await waitForElementVisible(byId('switch-environment-production-active'));
    await waitForElementVisible(byId('feature-switch-0-off'));

    log('Clear down features');
    await deleteFeature(1, 'header_size');
    await deleteFeature(0, 'header_enabled');

    log('Segment age rules');
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

    log('Add segment trait for user');
    await gotoTraits();
    await createTrait(0, 'age', 18);

    log('Check user now belongs to segment');
    await assertTextContent(byId('segment-0-name'), '18_or_19');

    log('Delete segment trait for user');
    await deleteTrait(0);

    log('Delete segment');
    await gotoSegments();
    await deleteSegment(0, '18_or_19');
});
