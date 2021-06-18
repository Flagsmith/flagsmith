/* eslint-disable no-unused-expressions */
/* eslint-disable func-names */
const inviteEmail = 'bullet-train@mailinator.com';
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
    '[Invite Tests] - Accept invite': function (browser) {
        let inviteUrl;
        browser.pause(10000); // now we throttle emails
        browser
            .url('https://www.mailinator.com/v3/index.jsp?zone=public&query=bullet-train#/#inboxpane')
            .useXpath()
            .waitForElementVisible(`//tbody/tr/td/a[contains(text(),"${`Bullet Train Org${append}`}")]`, 60000)
            .click(`//tbody/tr/td/a[contains(text(),"${`Bullet Train Org${append}`}")]`)
            .useCss()
            .waitForElementVisible('#msg_body')
            .pause(1000) // TODO revise this. currently necessary as the msg_body does not appear to show text immediately leading to an empty result
            .frame('msg_body')
            .getText('body', (res) => {
                console.log(res.value);
                inviteUrl = res.value.match(/(https?[^.]*)/g)[0];
                console.log('Invite URL:', inviteUrl);
                browser.url(inviteUrl)
                    .pause(200) // Allows the dropdown to fade in
                    .waitAndClick('#existing-member-btn')
                    .waitForElementVisible('#login-btn')
                    .waitAndSet('[name="email"]', inviteEmail)
                    .waitAndSet('[name="password"]', 'nightwatch')
                    .waitForElementVisible('#login-btn')
                    .click('#login-btn');
                browser
                    .useXpath()
                    .waitForElementPresent(`//div[contains(@class, "org-nav")]//a[contains(text(),"${`Bullet Train Org${append}`}")]`);
            });
    },
    '[Invite Tests] - Finish': function (browser) {
        browser
            .useCss();
        helpers.logout(browser);
    },
};
