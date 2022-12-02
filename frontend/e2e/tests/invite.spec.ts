import {test, expect} from '@playwright/test';
import {
    assertTextContent,
    byId,
    click,
    getInputValue,
    getText,
    log,
    login,
    setText,
    waitForElementVisible
} from "./helpers.e2e";
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;
const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;

test('Invite', async ({page}) => {
    await page.goto(url);
    log('Login', 'Invite Test');
    await login(email, password,page);
    log('Get Invite url', 'Invite Test');
    await page.goto('http://localhost:'+(process.env.PORT || 8080)+'/organisation-settings');
    const organisationName = getInputValue(byId('organisation-name'),page)
    const inviteLink = await getInputValue(byId('invite-link'),page)
    log('Accept invite', 'Invite Test');
    await page.goto(inviteLink);
    await setText('[name="email"]', inviteEmail,page);
    await setText(byId('firstName'), 'Bullet',page); // visit the url
    await setText(byId('lastName'), 'Train',page);
    await setText(byId('email'), inviteEmail,page);
    await setText(byId('password'), password,page);
    await waitForElementVisible(byId('signup-btn'),page);
    await click(byId('signup-btn'),page);
    await assertTextContent('.nav-link-featured', organisationName,page);
});
