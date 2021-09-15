const _ = require('lodash');

const byId = id => `[data-test="${id}"]`;
const testHelpers = {
    logout: (browser) => {
        browser
            .waitForElementNotPresent('.toast-message', 10000)
            .waitForElementVisible('#org-menu')
            .click('#org-menu')
            .waitForElementVisible('#logout-link')
            .pause(200) // Allows the dropdown to fade in
            .click('#logout-link')
            .expect.element(testHelpers.byTestID('email')).to.be.visible;
    },
    byTestID: byId,
    login: async (browser, url, email, password, retryOnFail) => {
        browser.url(url)
            .pause(200) // Allows the dropdown to fade in
            .waitAndSet('[name="email"]', `${email}`)
            .waitAndSet('[name="password"]', password)
            .click('#login-btn')
            .waitForElementVisible('#project-select-page');
    },
    waitLoggedIn: async (browser) => {
        browser.waitForElementNotPresent('#login-btn');
        browser.waitForElementNotPresent('.loader');
    },
    setSegmentRule(browser, ruleIndex, orIndex, name, operator, value) {
        browser.waitAndSet(testHelpers.byTestID(`rule-${ruleIndex}-property-${orIndex}`), name);
        if (operator) {
            browser.waitAndSet(testHelpers.byTestID(`rule-${ruleIndex}-operator-${orIndex}`), operator);
        }
        browser.waitAndSet(testHelpers.byTestID(`rule-${ruleIndex}-value-${orIndex}`), value);
    },
    deleteFeature(browser, index, name) {
        browser
            .waitForElementNotPresent('#create-feature-modal')
            .waitAndClick(byId(`remove-feature-btn-${index}`))
            .waitForElementPresent('#confirm-remove-feature-modal')
            .waitAndSet('[name="confirm-feature-name"]', name)
            .click('#confirm-remove-feature-btn')
            .waitForElementNotPresent('#confirm-remove-feature-modal')
            .waitForElementNotPresent(byId(`remove-feature-btn-${index}`));
    },
    deleteTrait(browser, index) {
        browser.waitAndClick(byId(`delete-user-trait-${index}`))
            .waitAndClick('#confirm-btn-yes')
            .waitForElementNotPresent(byId(`user-trait-${index}`));
    },
    deleteSegment(browser, index, name) {
        browser.waitAndClick(byId(`remove-segment-btn-${index}`))
            .waitForElementVisible('#confirm-remove-segment-modal')
            .waitForElementVisible('[name="confirm-segment-name"]')
            .setValue('[name="confirm-segment-name"]', name)
            .click('#confirm-remove-segment-btn')
            .waitForElementNotPresent('#confirm-segment-feature-modal')
            .waitForElementNotPresent(byId(`remove-segment-btn-${index}`));
    },
    toggleFeature(browser, index, toValue) {
        browser
            .waitForElementNotPresent('#confirm-remove-feature-modal')
            .pause(400) // Additional wait here as it seems rc-switch can be unresponsive for a while
            .waitAndClick(byId(`feature-switch-${index}${toValue ? '-off' : 'on'}`))
            .waitForElementPresent('#confirm-toggle-feature-modal')
            .waitAndClick('#confirm-toggle-feature-btn')
            .waitForElementNotPresent('#confirm-toggle-feature-modal')
            .waitForElementVisible(byId(`feature-switch-${index}${toValue ? '-on' : 'off'}`));
    },
    createRemoteConfig(browser, index, name, value, description = 'description') {
        const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
        testHelpers.gotoFeatures(browser);
        browser
            .waitForElementNotPresent('#create-feature-modal')
            .waitAndClick('#show-create-feature-btn');
        browser.waitAndSet(byId('featureID'), name)
            .waitAndSet(byId('featureValue'), value)
            .waitAndSet(byId('featureDesc'), description)
            .click(byId('create-feature-btn'))
            .waitForElementNotPresent('#create-feature-modal')
            .waitForElementVisible(byId(`feature-value-${index}`))
            .expect.element(byId(`feature-value-${index}`)).text.to.equal(expectedValue);
    },
    viewFeature(browser, index) {
        browser.waitAndClick(byId(`feature-item-${index}`))
            .waitForElementVisible('#create-feature-modal');
    },
    createFeature(browser, index, name, value, description = 'description') {
        browser
            .waitForElementNotPresent('#create-feature-modal')
            .click('#show-create-feature-btn')
            .waitAndSet('[name="featureID"]', name)
            .waitAndSet('[name="featureDesc"]', description);

        if (value) {
            browser.click(byId('toggle-feature-button'));
        }

        browser.click('#create-feature-btn')
            .waitForElementVisible(byId(`feature-item-${index}`));
    },
    saveFeature(browser) {
        browser.pause(400);
        browser.click('#update-feature-btn')
            .waitForElementNotPresent('#create-feature-modal');
    },
    gotoSegments(browser) {
        browser.waitAndClick('#segments-link')
            .pause(100);
    },
    gotoTraits(browser) {
        browser
            .waitAndClick('#users-link')
            .pause(500)
            .waitAndClick(byId('user-item-0'))
            .waitForElementVisible('#add-trait')
            .pause(100);
    },
    gotoFeatures(browser) {
        browser
            .waitAndClick('#features-link')
            .waitForElementVisible('#show-create-feature-btn')
            .pause(100);
    },
    gotoFeature(browser, index) {
        browser.click(byId(`feature-item-${index}`))
            .waitForElementPresent('#create-feature-modal');
        browser.pause(200);
    },
    createTrait(browser, index, id, value) {
        browser
            .waitAndClick('#add-trait')
            .waitForElementPresent('#create-trait-modal')
            .waitAndSet('[name="traitID"]', id)
            .waitAndSet('[name="traitValue"]', value)
            .click('#create-trait-btn')
            .waitForElementNotPresent('#create-trait-modal')
            .waitForElementVisible(byId(`user-trait-value-${index}`));
        const expectedValue = typeof value === 'string' ? `"${value}"` : `${value}`;
        browser.expect.element(byId(`user-trait-value-${index}`)).text.to.equal(expectedValue);
    },
    addSegmentOverride: (browser, index, value, selectionIndex = 0) => {
        browser.waitAndClick(byId('overrides'));
        browser.waitAndClick(byId(`select-segment-option-${selectionIndex}`));
        browser.waitForElementVisible(byId(`segment-override-${0}`));
        browser.pause(2000);
        if (value) {
            browser.waitAndClick(`${byId(`segment-override-${0}`)} [role="switch"]`);
        }
        browser.pause(200);
    },
    goToUser(browser, index) {
        browser
            .waitAndClick('#users-link')
            .pause(500)
            .waitAndClick(byId(`user-item-${index}`));
    },
    addSegmentOverrideConfig: (browser, index, value, selectionIndex = 0) => {
        browser.waitAndClick(byId('overrides'));
        browser.waitAndClick(byId(`select-segment-option-${selectionIndex}`));
        browser.pause(500);
        browser.waitForElementVisible(byId(`segment-override-value-${index}`));
        browser.waitAndSet(byId(`segment-override-value-${0}`), value);
    },
    setSegmentOverrideIndex: (browser, index, newIndex) => {
        browser.waitAndClick(byId('overrides'));
        browser.pause(2000);
        browser.waitAndSet(byId(`sort-${index}`), `${newIndex}`);
        browser.pause(2000);
    },
    createSegment: (browser, index, id, rules) => {
        const setSegmentRule = testHelpers.setSegmentRule;

        browser
            .waitAndClick(byId('show-create-segment-btn'));
        browser.waitAndSet(byId('segmentID'), id);
        _.each(rules, (rule, ruleIndex) => {
            if (ruleIndex > 0) {
                browser.waitAndClick(byId('add-rule'));
            }
            testHelpers.setSegmentRule(browser, ruleIndex, 0, rule.name, rule.operator, rule.value);
            _.each(rule.ors, (or, orIndex) => {
                browser.click(byId(`rule-${ruleIndex}-or`));
                setSegmentRule(browser, ruleIndex, orIndex + 1, or.name, or.operator, or.value);
            });
        });
        // Create
        browser.waitAndClick(byId('create-segment'))
            .waitForElementVisible(byId(`segment-${index}-name`))
            .expect.element(byId(`segment-${index}-name`)).text.to.equal(id);
    },
};
module.exports = testHelpers;
