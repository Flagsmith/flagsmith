// ``;/* eslint-disable func-names */
// const expect = require('chai').expect;
// const helpers = require('../helpers');
//
// const email = 'nightwatch@solidstategroup.com';
// const password = 'str0ngp4ssw0rd!';
// const byId = helpers.byTestID;
// const url = `http://localhost:${process.env.PORT || 8080}`;
//
// module.exports = {
//     // FEATURES
//     '[Features Tests] - Create feature': function (browser) {
//         testHelpers.login(browser, url, email, password);
//         browser.waitAndClick('#project-select-0');
//         testHelpers.createRemoteConfig(browser, 0, 'header_size', 'big');
//     },
//     '[Features Tests] - Create feature 2': function (browser) {
//         testHelpers.createFeature(browser, 1, 'header_enabled', false);
//     },
//     '[Features Tests] - Create feature 3 and remove it': function (browser) {
//         testHelpers.createFeature(browser, 2, 'short_life_feature', false);
//         testHelpers.deleteFeature(browser, 2, 'short_life_feature');
//     },
//     '[Features Tests] - Toggle feature on': function (browser) {
//         testHelpers.toggleFeature(browser, 0, true);
//     },
//     '[Features Tests] - Try feature out': function (browser) {
//         browser.waitForElementNotPresent('#confirm-toggle-feature-modal')
//             .pause(200)
//             .waitAndClick('#try-it-btn')
//             .waitForElementVisible('#try-it-results')
//             .getText('#try-it-results', (res) => {
//                 browser.assert.equal(typeof res, 'object');
//                 browser.assert.equal(res.status, 0);
//                 let json;
//                 try {
//                     json = JSON.parse(res.value);
//                 } catch (e) {
//                     throw new Error('Try it results are not valid JSON');
//                 }
//                 // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
//                 expect(json).to.have.property('header_size');
//                 expect(json.header_size).to.have.property('value');
//                 expect(json.header_size.value).to.equal('big');
//                 browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
//             });
//     },
//     '[Features Tests] - Change feature value to number': function (browser) {
//         browser
//             .refresh()
//             .pause(5000)
//             .waitAndClick(byId('feature-item-1'))
//             .waitForElementPresent('#create-feature-modal')
//             .pause(500)
//             .waitAndSet(byId('featureValue'), '12')
//             .pause(500)
//             .click('#update-feature-btn')
//             .waitForElementNotPresent('#create-feature-modal')
//             .waitForElementVisible(byId('feature-value-1'))
//             .expect.element(byId('feature-value-1')).text.to.equal('12');
//     },
//     '[Features Tests] - Try feature out should return numeric value': function (browser) {
//         browser
//             .refresh()
//             .waitForElementNotPresent('#create-feature-modal')
//             .pause(10000)
//             .waitForElementVisible('#try-it-btn')
//             .click('#try-it-btn')
//             .waitForElementVisible('#try-it-results')
//             .getText('#try-it-results', (res) => {
//                 browser.assert.equal(typeof res, 'object');
//                 browser.assert.equal(res.status, 0);
//                 let json;
//                 try {
//                     json = JSON.parse(res.value);
//                 } catch (e) {
//                     throw new Error('Try it results are not valid JSON');
//                 }
//                 // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
//                 expect(json).to.have.property('header_size');
//                 expect(json.header_size).to.have.property('value');
//                 expect(json.header_size.value).to.equal(12);
//                 expect(json.header_enabled).to.have.property('enabled');
//                 expect(json.header_enabled.enabled).to.equal(true);
//                 browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
//             });
//     },
//     '[Features Tests] - Change feature value to boolean': function (browser) {
//         browser
//             .waitAndClick(byId('feature-item-1'))
//             .waitForElementPresent('#create-feature-modal')
//             .waitAndSet(byId('featureValue'), 'false')
//             .waitAndClick('#update-feature-btn')
//             .waitForElementNotPresent('#create-feature-modal')
//             .waitForElementVisible(byId('feature-value-1'))
//             .expect.element(byId('feature-value-1')).text.to.equal('false');
//     },
//     '[Features Tests] - Try feature out should return boolean value': function (browser) {
//         browser
//             .refresh()
//             .waitForElementNotPresent('#create-feature-modal')
//             .waitForElementVisible('#try-it-btn')
//             .pause(10000) // wait for cache to expire, todo: remove when api has shared cache
//             .click('#try-it-btn')
//             .waitForElementVisible('#try-it-results')
//             .getText('#try-it-results', (res) => {
//                 browser.assert.equal(typeof res, 'object');
//                 browser.assert.equal(res.status, 0);
//                 let json;
//                 try {
//                     json = JSON.parse(res.value);
//                 } catch (e) {
//                     throw new Error('Try it results are not valid JSON');
//                 }
//                 // Unfortunately chai.js expect assertions do not report success in the Nightwatch reporter (but they do report failure)
//                 expect(json).to.have.property('header_size');
//                 expect(json.header_size).to.have.property('value');
//                 expect(json.header_size.value).to.equal(false);
//                 expect(json.header_enabled).to.have.property('enabled');
//                 expect(json.header_enabled.enabled).to.equal(true);
//                 browser.assert.ok(true, 'Try it JSON was correct for the feature'); // Re-assurance that the chai tests above passed
//             });
//     },
//     '[Features Tests] - Switch environment': function (browser) {
//         browser
//             .waitAndClick(byId('switch-environment-production'))
//             .waitForElementVisible(byId('switch-environment-production-active'));
//     },
//     '[Features Tests] - Feature should be off under different environment': function (browser) {
//         browser.waitForElementVisible(byId('feature-switch-0-off'));
//     },
//     '[Features Tests] - Clear down features': function (browser) {
//         testHelpers.deleteFeature(browser, 1, 'header_size');
//         testHelpers.deleteFeature(browser, 0, 'header_enabled');
//     },
//     // // Age == 18 || Age == 19
//     '[Segments Tests] - Create Segment': function (browser) {
//         testHelpers.gotoSegments(browser);
//
//         // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
//         // Rule 1- Age === 18 || Age === 19
//
//         testHelpers.createSegment(browser, 0, '18_or_19', [
//             // rule 2 =18 || =17
//             {
//                 name: 'age',
//                 operator: 'EQUAL',
//                 value: 18,
//                 ors: [
//                     {
//                         name: 'age',
//                         operator: 'EQUAL',
//                         value: 17,
//                     },
//                 ],
//             },
//             // rule 2 >17 or <10
//             {
//                 name: 'age',
//                 operator: 'GREATER_THAN',
//                 value: 17,
//                 ors: [
//                     {
//                         name: 'age',
//                         operator: 'LESS_THAN',
//                         value: 10,
//                     },
//                 ],
//             },
//             // rule 3 !=20
//             {
//                 name: 'age',
//                 operator: 'NOT_EQUAL',
//                 value: 20,
//             },
//             // Rule 4 <= 18
//             {
//                 name: 'age',
//                 operator: 'LESS_THAN_INCLUSIVE',
//                 value: 18,
//             },
//             // Rule 5 >= 18
//             {
//                 name: 'age',
//                 operator: 'GREATER_THAN_INCLUSIVE',
//                 value: 18,
//             },
//         ]);
//     },
//     '[Segments Tests] - Add segment trait for user': function (browser) {
//         testHelpers.gotoTraits(browser);
//         testHelpers.createTrait(browser, 0, 'age', 18);
//     },
//     '[Segments Tests] - Check user now belongs to segment': function (browser) {
//         browser.waitForElementVisible(byId('segment-0-name'));
//         browser.expect.element(byId('segment-0-name')).text.to.equal('18_or_19');
//     },
//     '[Segments Tests] - Delete segment trait for user': function (browser) {
//         testHelpers.deleteTrait(browser, 0);
//     },
//     '[Segments Tests] - Delete segment': function (browser) {
//         testHelpers.gotoSegments(browser);
//         testHelpers.deleteSegment(browser, 0, '18_or_19');
//     },
//     '[Segments Priority Tests] - Create segments': function (browser) {
//         testHelpers.gotoSegments(browser);
//         testHelpers.createSegment(browser, 0, 'segment_1', [
//             {
//                 name: 'trait',
//                 operator: 'EQUAL',
//                 value: '1',
//             },
//         ]);
//         testHelpers.createSegment(browser, 1, 'segment_2', [
//             {
//                 name: 'trait2',
//                 operator: 'EQUAL',
//                 value: '2',
//             },
//         ]);
//         testHelpers.createSegment(browser, 2, 'segment_3', [
//             {
//                 name: 'trait3',
//                 operator: 'EQUAL',
//                 value: '3',
//             },
//         ]);
//     },
//     '[Segments Priority Tests] - Create features': function (browser) {
//         testHelpers.gotoFeatures(browser);
//         testHelpers.createFeature(browser, 0, 'flag');
//         testHelpers.createRemoteConfig(browser, 0, 'config', 0);
//     },
//     '[Segments Priority Tests] - Set segment overrides features': function (browser) {
//         testHelpers.viewFeature(browser, 0);
//         testHelpers.addSegmentOverrideConfig(browser, 0, 3, 2);
//         testHelpers.addSegmentOverrideConfig(browser, 1, 2, 1);
//         testHelpers.addSegmentOverrideConfig(browser, 2, 1, 0);
//         testHelpers.saveFeature(browser);
//
//         testHelpers.viewFeature(browser, 1);
//         testHelpers.addSegmentOverride(browser, 0, true, 2);
//         testHelpers.addSegmentOverride(browser, 1, false, 1);
//         testHelpers.addSegmentOverride(browser, 2, true, 0);
//         testHelpers.saveFeature(browser);
//     },
//     '[Segments Priority Tests] - Set user in segment_1': function (browser) {
//         testHelpers.goToUser(browser, 0);
//         testHelpers.createTrait(browser, 0, 'trait', 1);
//         testHelpers.createTrait(browser, 1, 'trait2', 2);
//         testHelpers.createTrait(browser, 2, 'trait3', 3);
//         browser.waitForElementVisible(byId('segment-0-name'));
//         browser.expect.element(byId('segment-0-name')).text.to.equal('segment_1');
//         browser.waitForElementVisible(byId('user-feature-switch-1-on'));
//         browser.expect.element(byId('user-feature-value-0')).text.to.equal('1');
//     },
//     '[Segments Priority Tests] - Prioritise segment 2': function (browser) {
//         testHelpers.gotoFeatures(browser);
//         testHelpers.gotoFeature(browser, 0);
//         testHelpers.setSegmentOverrideIndex(browser, 1, 0);
//         testHelpers.saveFeature(browser);
//         testHelpers.gotoFeature(browser, 1);
//         testHelpers.setSegmentOverrideIndex(browser, 1, 0);
//         testHelpers.saveFeature(browser);
//         testHelpers.goToUser(browser, 0);
//         browser.expect.element(byId('user-feature-value-0')).text.to.equal('2');
//         browser.waitForElementVisible(byId('user-feature-switch-1-off'));
//     },
//     '[Segments Priority Tests] - Prioritise segment 3': function (browser) {
//         testHelpers.gotoFeatures(browser);
//         testHelpers.gotoFeature(browser, 0);
//         testHelpers.setSegmentOverrideIndex(browser, 2, 0);
//         testHelpers.saveFeature(browser);
//         testHelpers.gotoFeature(browser, 1);
//         testHelpers.setSegmentOverrideIndex(browser, 2, 0);
//         testHelpers.saveFeature(browser);
//         testHelpers.goToUser(browser, 0);
//         browser.expect.element(byId('user-feature-value-0')).text.to.equal('3');
//         browser.waitForElementVisible(byId('user-feature-switch-1-on'));
//     },
//     '[Segments Priority Tests] - Clear down features': function (browser) {
//         testHelpers.gotoFeatures(browser);
//         testHelpers.deleteFeature(browser, 1, 'flag');
//         testHelpers.deleteFeature(browser, 0, 'config');
//     },
//     '[Users Tests] - Create features': function (browser) {
//         testHelpers.gotoFeatures(browser);
//         testHelpers.createFeature(browser, 0, 'flag', true);
//         testHelpers.createRemoteConfig(browser, 0, 'config', 0);
//     },
//     '[Users Tests] - Toggle flag for user': function (browser) {
//         testHelpers.goToUser(browser, 0);
//
//         browser
//             .waitAndClick(byId('user-feature-switch-1-on'))
//             .waitAndClick('#confirm-toggle-feature-btn')
//             .waitForElementNotPresent('#confirm-toggle-feature-modal')
//             .waitForElementVisible(byId('user-feature-switch-1-off'));
//     },
//     '[Users Tests] - Edit flag for user': function (browser) {
//         browser
//             .pause(200)
//             .waitAndClick(byId('user-feature-0'))
//             .waitForElementPresent('#create-feature-modal')
//             .waitAndSet(byId('featureValue'), 'small')
//             .click('#update-feature-btn')
//             .waitForElementNotPresent('#create-feature-modal')
//             .expect.element(byId('user-feature-value-0')).text.to.equal('"small"');
//     },
//     '[Users Tests] - Toggle flag for user again': function (browser) {
//         browser
//             .pause(200) // Additional wait here as it seems rc-switch can be unresponsive for a while
//             .click(byId('user-feature-switch-1-off'))
//             .waitAndClick('#confirm-toggle-feature-btn')
//             .waitForElementNotPresent('#confirm-toggle-feature-modal')
//             .waitForElementVisible(byId('user-feature-switch-1-on'));
//     },
// };
