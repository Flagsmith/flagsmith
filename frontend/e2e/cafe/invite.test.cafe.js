import { Selector, t } from 'testcafe';
import {
    assertTextContent,
    byId,
    click,
    getLogger,
    log,
    login,
    logResults,
    setText,
    waitForElementVisible,
} from '../helpers.cafe';
import fetch from 'node-fetch';
import Project from '../../common/project';

const invitePrefix = `flagsmith${new Date().valueOf()}`;
const inviteEmail = `${invitePrefix}@restmail.net`;
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const logger = getLogger();

fixture`Invite Tests`
    .page`http://localhost:3000/`
    .requestHooks(logger);

test('Invite Test', async () => {
    log('Login', 'Invite Test');
    await login(email, password);
    const token = process.env.E2E_TEST_TOKEN
        ? process.env.E2E_TEST_TOKEN : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

    if (token) {
        await fetch(`${Project.api}e2etests/update-seats/`, {
            method: 'PUT',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-E2E-Test-Auth-Token': token.trim(),
            },
            body: JSON.stringify({seats:2}),
        }).then((res) => {
            if (res.ok) {
                // eslint-disable-next-line no-console
                console.log('\n', '\x1b[32m', 'update-seats successful', '\x1b[0m', '\n');
            } else {
                // eslint-disable-next-line no-console
                console.error('\n', '\x1b[31m', 'update-seats failed', res.status, '\x1b[0m', '\n');
            }
        });
    }
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
}).after(async (t) => {
    console.log('Start of Invite Requests');
    await logResults(logger.requests);
    console.log('End of Invite Errors');
});
