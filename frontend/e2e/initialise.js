let token;
const fetch = require('node-fetch');
const Project = require('../common/project');
const helpers = require('./helpers');

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/signup`;
const expect = require('chai').expect;

const cacheWait = 1000;
const byId = helpers.byTestID;

module.exports = {
    before: (browser, done) => {
        if (process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`]) {
            token = process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];
        }

        if (token) {
            fetch(`${Project.api}e2etests/teardown/`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-E2E-Test-Auth-Token': token.trim(),
                },
                body: JSON.stringify({}),
            }).then((res) => {
                if (res.ok) {
                    console.log('\n', '\x1b[32m', 'e2e teardown successful', '\x1b[0m', '\n');
                    done();
                } else {
                    console.error('\n', '\x1b[31m', 'e2e teardown failed', res.status, '\x1b[0m', '\n');
                }
            });
        } else {
            console.error('\n', '\x1b[31m', 'e2e teardown failed - no available token', '\x1b[0m', '\n');
        }
    },
    '[Initialise - Create Org]': (browser) => {
        browser.url(url)
            .waitAndSet(byId('firstName'), 'Bullet') // visit the url
            .waitAndSet(byId('lastName'), 'Train')
            .waitAndSet(byId('email'), email)
            .waitAndSet(byId('password'), password)
            .click(byId('signup-btn'))
            .waitAndSet('[name="orgName"]', 'Bullet Train Ltd')
            .click('#create-org-btn')
            .waitForElementVisible(byId('project-select-page'));

        browser.waitAndClick(byId('create-first-project-btn'))
            .waitAndSet(byId('projectName'), 'My Test Project')
            .click(byId('create-project-btn'))
            .waitForElementVisible(byId('features-page'));
    },
    '[Initialise Tests] - Create feature': function (browser) {
        testHelpers.createRemoteConfig(browser, 0, 'header_size', 'big');
    },
    '[Initialise Tests] - Create feature 2': function (browser) {
        testHelpers.createFeature(browser, 1, 'header_enabled', false);
    },
    '[Initialise Tests] - Create feature 3 and remove it': function (browser) {
        testHelpers.createFeature(browser, 2, 'short_life_feature', false);
        testHelpers.deleteFeature(browser, 2, 'short_life_feature');
    },
    '[Initialise Tests] - Toggle feature on': function (browser) {
        testHelpers.toggleFeature(browser, 0, true);
    },
    '[Initialise Tests] - Try feature out': function (browser) {
        browser.waitForElementNotPresent('#confirm-toggle-feature-modal')
            .pause(200)
            .waitAndClick('#try-it-btn')
            .waitForElementVisible('#try-it-results')
            .getText('#try-it-results', (res) => {
                browser.assert.equal(typeof res, 'object');
                browser.assert.equal(res.status, 0);
                let json;
                try {
                    json = JSON.parse(res.value);
                } catch (e) {
                    throw new Error('Try it results are not valid JSON');
                }
                // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
                expect(json).to.have.property('header_size');
                expect(json.header_size).to.have.property('value');
                expect(json.header_size.value).to.equal('big');
                browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
            });
    },
    '[Initialise Tests] - Change feature value to number': function (browser) {
        browser
            .refresh()
            .waitAndClick(byId('feature-item-1'))
            .waitForElementPresent('#create-feature-modal')
            .pause(500)
            .waitAndSet(byId('featureValue'), '12')
            .pause(500)
            .click('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible(byId('feature-value-1'))
            .expect.element(byId('feature-value-1')).text.to.equal('12');
    },
    '[Initialise Tests] - Try feature out should return numeric value': function (browser) {
        browser
            .refresh()
            .waitForElementNotPresent('#create-feature-modal')
            .pause(cacheWait)
            .waitForElementVisible('#try-it-btn')
            .click('#try-it-btn')
            .waitForElementVisible('#try-it-results')
            .getText('#try-it-results', (res) => {
                browser.assert.equal(typeof res, 'object');
                browser.assert.equal(res.status, 0);
                let json;
                try {
                    json = JSON.parse(res.value);
                } catch (e) {
                    throw new Error('Try it results are not valid JSON');
                }
                // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
                expect(json).to.have.property('header_size');
                expect(json.header_size).to.have.property('value');
                expect(json.header_size.value).to.equal(12);
                expect(json.header_enabled).to.have.property('enabled');
                expect(json.header_enabled.enabled).to.equal(true);
                browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
            });
    },
    '[Initialise Tests] - Change feature value to boolean': function (browser) {
        browser
            .waitAndClick(byId('feature-item-1'))
            .waitForElementPresent('#create-feature-modal')
            .waitAndSet(byId('featureValue'), 'false')
            .waitAndClick('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible(byId('feature-value-1'))
            .expect.element(byId('feature-value-1')).text.to.equal('false');
    },
    '[Initialise Tests] - Try feature out should return boolean value': function (browser) {
        browser
            .refresh()
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible('#try-it-btn')
            .pause(cacheWait) // wait for cache to expire, todo: remove when api has shared cache
            .click('#try-it-btn')
            .waitForElementVisible('#try-it-results')
            .getText('#try-it-results', (res) => {
                browser.assert.equal(typeof res, 'object');
                browser.assert.equal(res.status, 0);
                let json;
                try {
                    json = JSON.parse(res.value);
                } catch (e) {
                    throw new Error('Try it results are not valid JSON');
                }
                // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
                expect(json).to.have.property('header_size');
                expect(json.header_size).to.have.property('value');
                expect(json.header_size.value).to.equal(false);
                expect(json.header_enabled).to.have.property('enabled');
                expect(json.header_enabled.enabled).to.equal(true);
                browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
            });
    },
    '[Initialise Tests] - Switch environment': function (browser) {
        browser
            .waitAndClick(byId('switch-environment-production'))
            .waitForElementVisible(byId('switch-environment-production-active'));
    },
    '[Initialise Tests] - Feature should be off under different environment': function (browser) {
        browser.waitForElementVisible(byId('feature-switch-0-off'));
    },
    '[Initialise Tests] - Clear down features': function (browser) {
        testHelpers.deleteFeature(browser, 1, 'header_size');
        testHelpers.deleteFeature(browser, 0, 'header_enabled');
    },
    '[Initialise Tests] - Create Segment': function (browser) {
        testHelpers.gotoSegments(browser);

        // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
        // Rule 1- Age === 18 || Age === 19

        testHelpers.createSegment(browser, 0, '18_or_19', [
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
    },
    '[Initialise Tests] - Add segment trait for user': function (browser) {
        testHelpers.gotoTraits(browser);
        testHelpers.createTrait(browser, 0, 'age', 18);
    },
    '[Initialise Tests] - Check user now belongs to segment': function (browser) {
        browser.waitForElementVisible(byId('segment-0-name'));
        browser.expect.element(byId('segment-0-name')).text.to.equal('18_or_19');
    },
    '[Initialise Tests] - Delete segment trait for user': function (browser) {
        testHelpers.deleteTrait(browser, 0);
    },
    '[Initialise Tests] - Delete segment': function (browser) {
        testHelpers.gotoSegments(browser);
        testHelpers.deleteSegment(browser, 0, '18_or_19');
    },
};
