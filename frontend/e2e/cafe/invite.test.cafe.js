import { Selector, t } from 'testcafe';
import {
    assertTextContent,
    byId,
    click,
    log,
    login,
    setText,
    waitForElementVisible,
    waitForXPathElementVisible,
} from '../helpers.cafe';

const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
import checkConsoleMessages from '../check-console-messages'

fixture`Invite Tests`
    .page`http://localhost:3000/`
    .afterEach(async () => await checkConsoleMessages());

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
});
