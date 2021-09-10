const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;
const helpers = require('../helpers');

const byId = helpers.byTestID;

module.exports = {
    '[Project Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password);
        browser.waitAndClick('#project-select-0');
    },
    '[Project Tests] - Create environment': function (browser) {
        browser.waitAndClick('#create-env-link')
            .waitForElementPresent('#create-env-modal')
            .waitAndSet('[name="envName"]', 'Staging')
            .click('#create-env-btn')
            .waitForElementNotPresent('#create-env-modal')
            .waitForElementVisible(byId('switch-environment-staging-active'));
    },
    '[Project Tests] - Edit environment': function (browser) {
        browser
            .waitAndClick('#env-settings-link')
            .waitAndSet("[name='env-name']", 'Internal')
            .click('#save-env-btn');

        browser.waitForElementVisible(byId('switch-environment-staginginternal-active'));
    },
    '[Project Tests] - Delete environment': function (browser) {
        browser
            .waitAndClick('#delete-env-btn')
            .waitAndSet("[name='confirm-env-name']", 'StagingInternal')
            .click('#confirm-delete-env-btn')
            .waitForElementVisible(byId('features-page'));
        browser.url(`${url}projects`)
            .waitForElementVisible('#project-select-page');
    },
    '[Project Tests] - View project': function (browser) {
        browser.waitForElementVisible('#project-select-0');
        browser.expect.element('#project-select-0').text.to.equal('My Test Project');
        browser.click('#project-select-0');
        browser.waitForElementVisible('#features-page');
    },
    '[Project Tests] - Edit project': function (browser) {
        browser
            .waitForElementVisible('#project-settings-link')
            .pause(200) // Slide in transition
            .waitAndClick('#project-settings-link')
            .waitAndSet("[name='proj-name']", 'Test Project')
            .click('#save-proj-btn');

        browser.waitForElementVisible(byId('switch-project-test project-active'));
    },
};
