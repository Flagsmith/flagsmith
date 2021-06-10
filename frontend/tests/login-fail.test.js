/* eslint-disable func-names */
const helpers = require('./helpers');

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}`;

module.exports = {
    // 'Login should fail due to invalid email address': function (browser) {
    //     helpers.login(browser, url, 'bad-email', password);
    //     browser.expect.element('#error-alert').to.be.visible;
    // },
    // 'Login should fail due to wrong password': function (browser) {
    //     helpers.login(browser, url, email, 'bad-password');
    //     browser.expect.element('#error-alert').to.be.visible;
    //     browser.end();
    // },
};
