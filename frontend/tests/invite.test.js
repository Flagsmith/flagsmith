/* eslint-disable no-unused-expressions */
/* eslint-disable func-names */
const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}`;
const append = `${new Date().valueOf()}`;
const helpers = require('./helpers');

const byId = helpers.byTestID;

module.exports = {
    '[Invite Tests] - Login': function (browser) {
        testHelpers.login(browser, url, email, password);
    },
    '[Invite Tests] - Create organisation': function (browser) {
        testHelpers.waitLoggedIn(browser);
        browser.url(`${url}/create`);
        browser.waitForElementVisible('#create-org-page');

        browser
            .waitAndSet('[name="orgName"]', `Bullet Train Org${append}`)
            .click('#create-org-btn')
            .waitForElementVisible('#project-select-page')
            .assert.containsText('#org-menu', `Bullet Train Org${append}`);
    },
    '[Invite Tests] - Create project': function (browser) {
        browser
            .waitForElementVisible('#create-first-project-btn')
            .click('#create-first-project-btn')
            .waitAndSet('[name="projectName"]', 'My Test Project')
            .click(byId('create-project-btn'));

        browser.waitForElementVisible('#features-page');
    },
    '[Invite Tests] - Invite user': function (browser) {
        browser.pause(200);
        browser.url(`${url}/organisation-settings`);
        browser.waitAndClick('#btn-invite');
        browser.waitAndSet('[name="inviteEmail"]', inviteEmail);
        browser.waitAndSet(byId('select-role'), 'ADMIN');
        browser.click('#btn-send-invite');
        browser.waitForElementNotPresent('#btn-send-invite');
        browser.waitForElementVisible(byId('pending-invite-0'));
    },
    '[Invite Tests] - Invite user 2': function (browser) {
        browser.click('#btn-invite');
        browser.waitAndSet('[name="inviteEmail"]', 'test@test.com');
        browser.waitAndSet(byId('select-role'), 'USER');
        browser.click('#btn-send-invite')
            .waitForElementNotPresent('#btn-send-invite')
            .waitForElementVisible(byId('pending-invite-1'));
    },
    '[Invite Tests] - Delete user 2': function (browser) {
        browser
            .click(`${byId('pending-invite-1')} #delete-invite`)
            .waitForElementVisible('#confirm-btn-yes')
            .click('#confirm-btn-yes')
            .waitForElementNotPresent(byId('pending-invite-1'));
    },
    '[Invite Tests] - Accept invite via Restmail': function (browser) {
        var apiUrl = 'https://restmail.net/mail/' + invitePrefix
        browser.apiGet(apiUrl, function (response) {
            var jsonBody = JSON.parse(response.body)
            browser.assert.equal(response.statusCode, '200')
            var pattern = /<a[^>]*href=["']([^"']*)["']/g;
            var htmlBody = jsonBody[0].html;
            while (match = pattern.exec(htmlBody)) {
                browser.url(match[1])
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
                    .waitForElementPresent(`//div[contains(@class, "org-nav")]//a[contains(text(),"${`Bullet Train Org${append}`}")]`);
            }
        })
    },
    '[Invite Tests] - Finish': function (browser) {
        browser
            .useCss();
        helpers.logout(browser);
    },
};