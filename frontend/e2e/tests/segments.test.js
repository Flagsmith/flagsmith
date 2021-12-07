``;/* eslint-disable func-names */
const expect = require('chai').expect;
const helpers = require('../helpers');

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const byId = helpers.byTestID;
const url = `http://localhost:${process.env.PORT || 8080}`;

module.exports = {

    '[Segments Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password);
        browser.waitAndClick('#project-select-0');
    },

    '[Segments Priority Tests] - Create segments': function (browser) {
        testHelpers.gotoSegments(browser);
        testHelpers.createSegment(browser, 0, 'segment_1', [
            {
                name: 'trait',
                operator: 'EQUAL',
                value: '1',
            },
        ]);
        testHelpers.createSegment(browser, 1, 'segment_2', [
            {
                name: 'trait2',
                operator: 'EQUAL',
                value: '2',
            },
        ]);
        testHelpers.createSegment(browser, 2, 'segment_3', [
            {
                name: 'trait3',
                operator: 'EQUAL',
                value: '3',
            },
        ]);
    },
    '[Segments Priority Tests] - Create features': function (browser) {
        testHelpers.gotoFeatures(browser);
        testHelpers.createFeature(browser, 0, 'flag');
        testHelpers.createRemoteConfig(browser, 0, 'config', 0);
    },
    '[Segments Priority Tests] - Set segment overrides features': function (browser) {
        testHelpers.viewFeature(browser, 0);
        testHelpers.addSegmentOverrideConfig(browser, 0, 3, 2);
        testHelpers.addSegmentOverrideConfig(browser, 1, 2, 1);
        testHelpers.addSegmentOverrideConfig(browser, 2, 1, 0);
        testHelpers.saveFeature(browser);

        testHelpers.viewFeature(browser, 1);
        testHelpers.addSegmentOverride(browser, 0, true, 2);
        testHelpers.addSegmentOverride(browser, 1, false, 1);
        testHelpers.addSegmentOverride(browser, 2, true, 0);
        testHelpers.saveFeature(browser);
    },
    '[Segments Priority Tests] - Set user in segment_1': function (browser) {
        testHelpers.goToUser(browser, 0);
        testHelpers.createTrait(browser, 0, 'trait', 1);
        testHelpers.createTrait(browser, 1, 'trait2', 2);
        testHelpers.createTrait(browser, 2, 'trait3', 3);
        browser.waitForElementVisible(byId('segment-0-name'));
        browser.expect.element(byId('segment-0-name')).text.to.equal('segment_1');
        browser.waitForElementVisible(byId('user-feature-switch-1-on'));
        browser.expect.element(byId('user-feature-value-0')).text.to.equal('1');
    },
    '[Segments Priority Tests] - Prioritise segment 2': function (browser) {
        testHelpers.gotoFeatures(browser);
        testHelpers.gotoFeature(browser, 0);
        testHelpers.setSegmentOverrideIndex(browser, 1, 0);
        testHelpers.saveFeature(browser);
        testHelpers.gotoFeature(browser, 1);
        testHelpers.setSegmentOverrideIndex(browser, 1, 0);
        testHelpers.saveFeature(browser);
        testHelpers.goToUser(browser, 0);
        browser.expect.element(byId('user-feature-value-0')).text.to.equal('2');
        browser.waitForElementVisible(byId('user-feature-switch-1-off'));
    },
    '[Segments Priority Tests] - Prioritise segment 3': function (browser) {
        testHelpers.gotoFeatures(browser);
        testHelpers.gotoFeature(browser, 0);
        testHelpers.setSegmentOverrideIndex(browser, 2, 0);
        testHelpers.saveFeature(browser);
        testHelpers.gotoFeature(browser, 1);
        testHelpers.setSegmentOverrideIndex(browser, 2, 0);
        testHelpers.saveFeature(browser);
        testHelpers.goToUser(browser, 0);
        browser.expect.element(byId('user-feature-value-0')).text.to.equal('3');
        browser.waitForElementVisible(byId('user-feature-switch-1-on'));
    },
    '[Segments Priority Tests] - Clear down features': function (browser) {
        testHelpers.gotoFeatures(browser);
        testHelpers.deleteFeature(browser, 1, 'flag');
        testHelpers.deleteFeature(browser, 0, 'config');
    },
    '[Users Tests] - Create features': function (browser) {
        testHelpers.gotoFeatures(browser);
        testHelpers.createFeature(browser, 0, 'flag', true);
        testHelpers.createRemoteConfig(browser, 0, 'config', 0);
    },
    '[Users Tests] - Toggle flag for user': function (browser) {
        testHelpers.goToUser(browser, 0);

        browser
            .waitAndClick(byId('user-feature-switch-1-on'))
            .waitAndClick('#confirm-toggle-feature-btn')
            .waitForElementNotPresent('#confirm-toggle-feature-modal')
            .waitForElementVisible(byId('user-feature-switch-1-off'));
    },
    '[Users Tests] - Edit flag for user': function (browser) {
        browser
            .pause(200)
            .waitAndClick(byId('user-feature-0'))
            .waitForElementPresent('#create-feature-modal')
            .waitAndSet(byId('featureValue'), 'small')
            .click('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal')
            .expect.element(byId('user-feature-value-0')).text.to.equal('"small"');
    },
    '[Users Tests] - Toggle flag for user again': function (browser) {
        browser
            .pause(200) // Additional wait here as it seems rc-switch can be unresponsive for a while
            .click(byId('user-feature-switch-1-off'))
            .waitAndClick('#confirm-toggle-feature-btn')
            .waitForElementNotPresent('#confirm-toggle-feature-modal')
            .waitForElementVisible(byId('user-feature-switch-1-on'));
    },
};
