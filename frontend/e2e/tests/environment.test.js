const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;
const helpers = require('../helpers');

const byId = helpers.byTestID;

module.exports = {
    '[Environment Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password, true);
        browser.waitAndClick('#project-select-0');
    },
    '[Environment Tests] - Create environment': function (browser) {
        browser.waitAndClick('#create-env-link')
            .waitForElementPresent('#create-env-modal')
            .waitAndSet('[name="envName"]', 'Staging')
            .click('#create-env-btn')
            .waitForElementNotPresent('#create-env-modal')
            .waitForElementVisible(byId('switch-environment-staging-active'));
    },
    '[Environment Tests] - Edit environment': function (browser) {
        browser
            .waitAndClick('#env-settings-link')
            .waitAndSet("[name='env-name']", 'Internal')
            .click('#save-env-btn');

        browser.waitForElementVisible(byId('switch-environment-staginginternal-active'));
    },
    '[Environment Tests] - Delete environment': function (browser) {
        browser
            .waitAndClick('#delete-env-btn')
            .waitAndSet("[name='confirm-env-name']", 'StagingInternal')
            .click('#confirm-delete-env-btn')
            .waitForElementVisible(byId('features-page'));
        browser.url(`${url}projects`)
            .waitForElementVisible('#project-select-page');
    },
};
