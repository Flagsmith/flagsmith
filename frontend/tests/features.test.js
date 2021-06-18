/* eslint-disable func-names */
const expect = require('chai').expect;
const helpers = require('./helpers');

const byId = helpers.byTestID;

module.exports = {
    // FEATURES
    '[Features Tests] - Create feature': function (browser) {
        testHelpers.createRemoteConfig(browser, 0, 'header_size', 'big');
    },
    '[Features Tests] - Create feature 2': function (browser) {
        testHelpers.createFeature(browser, 1, 'header_enabled', false);
    },
    '[Features Tests] - Create feature 3 and remove it': function (browser) {
        testHelpers.createFeature(browser, 2, 'short_life_feature', false);
        testHelpers.deleteFeature(browser, 2, 'short_life_feature');
    },
    '[Features Tests] - Toggle feature on': function (browser) {
        testHelpers.toggleFeature(browser, 0, true);
    },
    '[Features Tests] - Try feature out': function (browser) {
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
    '[Features Tests] - Change feature value to number': function (browser) {
        browser
            .refresh()
            .waitAndClick(byId('feature-item-1'))
            .waitForElementVisible('#create-feature-modal')
            .waitForElementVisible(byId('featureValue'))
            .pause(200)
            .clearValue(byId('featureValue'))
            .pause(500)
            .setValue(byId('featureValue'), '12')
            .pause(500)
            .click('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible(byId('feature-value-1'))
            .expect.element(byId('feature-value-1')).text.to.equal('12');
    },
    '[Features Tests] - Try feature out should return numeric value': function (browser) {
        browser
            .refresh()
            .waitForElementNotPresent('#create-feature-modal')
            .pause(10000)
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
    '[Features Tests] - Change feature value to boolean': function (browser) {
        browser
            .waitAndClick(byId('feature-item-1'))
            .waitForElementPresent('#create-feature-modal')
            .waitForElementVisible(byId('featureValue'))
            .pause(200)
            .clearValue(byId('featureValue'))
            .pause(50)
            .setValue(byId('featureValue'), 'false')
            .pause(50)
            .click('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible(byId('feature-value-1'))
            .expect.element(byId('feature-value-1')).text.to.equal('false');
    },
    '[Features Tests] - Try feature out should return boolean value': function (browser) {
        browser
            .refresh()
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible('#try-it-btn')
            .pause(10000) // wait for cache to expire, todo: remove when api has shared cache
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
    '[Features Tests] - Switch environment': function (browser) {
        browser
            .waitAndClick(byId('switch-environment-production'))
            .waitForElementVisible(byId('switch-environment-production-active'));
    },
    '[Features Tests] - Feature should be off under different environment': function (browser) {
        browser.waitForElementVisible(byId('feature-switch-0-off'));
    },
    '[Features Tests] - Clear down features': function (browser) {
        testHelpers.deleteFeature(browser, 1, 'header_size');
        testHelpers.deleteFeature(browser, 0, 'header_enabled');
    },
};