/* eslint-disable func-names */
const url = `http://localhost:${process.env.PORT || 8080}`;

module.exports = {
    '[Initial Cleanup Tests] - Delete Bullet Train Ltd organisation': function (browser) {
        browser
            .url(`${url}/organisation-settings`)
            .waitForElementVisible('#delete-org-btn')
            .click('#delete-org-btn')
            .waitForElementVisible('[name="confirm-org-name"]')
            .setValue('[name="confirm-org-name"]', 'Bullet Train Ltd')
            .click('#confirm-del-org-btn')
            .waitForElementVisible('#create-org-page');
        browser.end();
    },
};
