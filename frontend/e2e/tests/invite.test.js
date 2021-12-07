/* eslint-disable no-unused-expressions */
/* eslint-disable func-names */
const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}`;
const append = `${new Date().valueOf()}`;
const helpers = require('../helpers');

const byId = helpers.byTestID;
let inviteLink;
let organistationName;
module.exports = {
    '[Invite Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password, true);
    },
    '[Invite Tests] - Invite user': function (browser) {
        browser.pause(200);
        browser.url(`${url}/organisation-settings`);
        browser.waitForElementVisible(byId('organisation-name'))
            .getValue(byId('organisation-name'), (result) => {
                organistationName = result.value;
            });
        browser.waitForElementVisible(byId('invite-link'))
            .getValue(byId('invite-link'), (result) => {
                inviteLink = result.value;
            });
    },
    '[Invite Tests] - Accept invite': function (browser) {
        browser.url(inviteLink)
            .pause(200) // Allows the dropdown to fade in
            .waitForElementVisible(byId('signup-btn'))
            .waitAndSet('[name="email"]', inviteEmail)
            .waitAndSet(byId('firstName'), 'Bullet') // visit the url
            .waitAndSet(byId('lastName'), 'Train')
            .waitAndSet(byId('email'), inviteEmail)
            .waitAndSet(byId('password'), password)
            .waitForElementVisible(byId('signup-btn'))
            .click(byId('signup-btn'));
        browser
            .useXpath()
            .waitForElementPresent(`//div[contains(@class, "org-nav")]//a[contains(text(),"${`${organistationName}`}")]`);
    },
    '[Invite Tests] - Finish': function (browser) {
        browser
            .useCss();
        helpers.logout(browser);
    },
};
