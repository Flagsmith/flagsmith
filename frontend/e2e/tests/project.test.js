const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;
const helpers = require('../helpers');

const byId = helpers.byTestID;

module.exports = {
    '[Project Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password, true);
    },
    '[Project Tests] - View project': function (browser) {
        browser.waitForElementVisible('#project-select-0');
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
