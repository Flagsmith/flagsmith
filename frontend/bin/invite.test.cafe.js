import { Selector, t } from 'testcafe';
import {
    assertTextContent,
    byId,
    click,
    getLogger,
    log,
    login,
    setText,
    waitForElementVisible,
    waitForXPathElementVisible,
} from '../e2e/helpers.cafe';

const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const logger = getLogger()

fixture`Invite Tests`
    .page`http://localhost:3000/`
    .requestHooks(logger)

test('Invite Test', async () => {
    log('Login', 'Invite Test');
    await login(email, password);
    log('Get Invite url', 'Invite Test');
    await t.navigateTo('http://localhost:3000/organisation-settings');
    const organisationName = await Selector(byId('organisation-name')).value;
    const inviteLink = await Selector(byId('invite-link')).value;
    log('Accept invite', 'Invite Test');
    await t.navigateTo(inviteLink);
    await setText('[name="email"]', inviteEmail);
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train');
    await setText(byId('email'), inviteEmail);
    await setText(byId('password'), password);
    await waitForElementVisible(byId('signup-btn'));
    await click(byId('signup-btn'));
    await assertTextContent('.nav-link-featured', organisationName);
}).after(async (t)=>{
    console.log("Start of Invite Requests")
    console.log(JSON.stringify(logger.requests, null,2))
    console.log("End of Invite Requests")
    console.log("Start of Invite Errors")
    console.error(JSON.stringify((await t.getBrowserConsoleMessages()).error));
    console.log("End of Invite Errors")

})

