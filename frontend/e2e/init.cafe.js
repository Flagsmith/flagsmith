import { t, Selector } from 'testcafe';
import fetch from 'node-fetch';
import Project from '../common/project';
import {
    assertTextContent,
    byId,
    createFeature,
    createRemoteConfig,
    deleteFeature, getText,
    setText,
    toggleFeature,
    waitForElementVisible,
} from './helpers.cafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/signup`;

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

// eslint-disable-next-line no-console
const log = message => console.log('\n', '\x1b[32m', message, '\x1b[0m', '\n');

test('[Initialise]', async () => {
    log('Create Organisation');
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train'); // visit the url
    await setText(byId('email'), email); // visit the url
    await setText(byId('password'), password); // visit the url
    await t.click(byId('signup-btn'));
    await setText('[name="orgName"]', 'Bullet Train Ltd');
    await t.click('#create-org-btn')
        .expect(Selector(byId('project-select-page')).visible)
        .ok();
    log('Create Project');
    await t.click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await t.click(byId('create-project-btn'));
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
    await t.click('#try-it-btn');
    let text = await getText('#try-it-results');
    let json;
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql('big');
    await t.expect(json.header_enabled.enabled).eql(true);
    await t.eval(() => location.reload(true));
    log('Update feature');
    await t.click(byId('feature-item-1'));
    await setText(byId('featureValue'), '12');
    await t.click('#update-feature-btn');
    await assertTextContent(byId('feature-value-1'), '12');
    log('Try it again');
    await t.click('#try-it-btn');
    text = await getText('#try-it-results');
    try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
    await t.expect(json.header_size.value).eql(12);
});

// '[Initialise Tests] - Change feature value to boolean': function (browser) {
//     browser
//         .waitAndClick(byId('feature-item-1'))
//         .waitForElementPresent('#create-feature-modal')
//         .waitAndSet(byId('featureValue'), 'false')
//         .waitAndClick('#update-feature-btn')
//         .waitForElementNotPresent('#create-feature-modal')
//         .waitForElementVisible(byId('feature-value-1'))
//         .expect.element(byId('feature-value-1')).text.to.equal('false');
// },
// '[Initialise Tests] - Try feature out should return boolean value': function (browser) {
//     browser
//         .refresh()
//         .waitForElementNotPresent('#create-feature-modal')
//         .waitForElementVisible('#try-it-btn')
//         .pause(cacheWait) // wait for cache to expire, todo: remove when api has shared cache
//         .click('#try-it-btn')
//         .waitForElementVisible('#try-it-results')
//         .getText('#try-it-results', (res) => {
//             browser.assert.equal(typeof res, 'object');
//             browser.assert.equal(res.status, 0);
//             let json;
//             try {
//                 json = JSON.parse(res.value);
//             } catch (e) {
//                 throw new Error('Try it results are not valid JSON');
//             }
//             // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
//             expect(json).to.have.property('header_size');
//             expect(json.header_size).to.have.property('value');
//             expect(json.header_size.value).to.equal(false);
//             expect(json.header_enabled).to.have.property('enabled');
//             expect(json.header_enabled.enabled).to.equal(true);
//             browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
//         });
// },
// '[Initialise Tests] - Switch environment': function (browser) {
//     browser
//         .waitAndClick(byId('switch-environment-production'))
//         .waitForElementVisible(byId('switch-environment-production-active'));
// },
// '[Initialise Tests] - Feature should be off under different environment': function (browser) {
//     browser.waitForElementVisible(byId('feature-switch-0-off'));
// },
// '[Initialise Tests] - Clear down features': function (browser) {
//     testHelpers.deleteFeature(browser, 1, 'header_size');
//     testHelpers.deleteFeature(browser, 0, 'header_enabled');
// },
// '[Initialise Tests] - Create Segment': function (browser) {
//     testHelpers.gotoSegments(browser);
//
//     // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
//     // Rule 1- Age === 18 || Age === 19
//
//     testHelpers.createSegment(browser, 0, '18_or_19', [
//         // rule 2 =18 || =17
//         {
//             name: 'age',
//             operator: 'EQUAL',
//             value: 18,
//             ors: [
//                 {
//                     name: 'age',
//                     operator: 'EQUAL',
//                     value: 17,
//                 },
//             ],
//         },
//         // rule 2 >17 or <10
//         {
//             name: 'age',
//             operator: 'GREATER_THAN',
//             value: 17,
//             ors: [
//                 {
//                     name: 'age',
//                     operator: 'LESS_THAN',
//                     value: 10,
//                 },
//             ],
//         },
//         // rule 3 !=20
//         {
//             name: 'age',
//             operator: 'NOT_EQUAL',
//             value: 20,
//         },
//         // Rule 4 <= 18
//         {
//             name: 'age',
//             operator: 'LESS_THAN_INCLUSIVE',
//             value: 18,
//         },
//         // Rule 5 >= 18
//         {
//             name: 'age',
//             operator: 'GREATER_THAN_INCLUSIVE',
//             value: 18,
//         },
//     ]);
// },
// '[Initialise Tests] - Add segment trait for user': function (browser) {
//     testHelpers.gotoTraits(browser);
//     testHelpers.createTrait(browser, 0, 'age', 18);
// },
// '[Initialise Tests] - Check user now belongs to segment': function (browser) {
//     browser.waitForElementVisible(byId('segment-0-name'));
//     browser.expect.element(byId('segment-0-name')).text.to.equal('18_or_19');
// },
// '[Initialise Tests] - Delete segment trait for user': function (browser) {
//     testHelpers.deleteTrait(browser, 0);
// },
// '[Initialise Tests] - Delete segment': function (browser) {
//     testHelpers.gotoSegments(browser);
//     testHelpers.deleteSegment(browser, 0, '18_or_19');
// },
