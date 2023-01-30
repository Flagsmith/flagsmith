import { t } from 'testcafe';
import fetch from 'node-fetch';
import Project from '../common/project';
import {
    assertTextContent,
    byId, click, closeModal,
    getLogger,
    createFeature,
    createRemoteConfig, createSegment, createTrait,
    deleteFeature, deleteSegment, deleteTrait, getText, gotoSegments, gotoTraits, log,
    setText,
    toggleFeature,
    waitForElementVisible, gotoFeatures, gotoFeature, addSegmentOverride, waitAndRefresh, logResults,
} from './helpers.cafe';

require('dotenv').config();

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;
const logger = getLogger();
fixture`Initialise`
    .requestHooks(logger)
    .before(async () => {
        const token = process.env.E2E_TEST_TOKEN
            ? process.env.E2E_TEST_TOKEN : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

        if (token) {
            await fetch(`${Project.api}e2etests/teardown/`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-E2E-Test-Auth-Token': token.trim(),
                },
                body: JSON.stringify({}),
            }).then((res) => {
                if (res.ok) {
                    // eslint-disable-next-line no-console
                    console.log('\n', '\x1b[32m', 'e2e teardown successful', '\x1b[0m', '\n');
                } else {
                    // eslint-disable-next-line no-console
                    console.error('\n', '\x1b[31m', 'e2e teardown failed', res.status, '\x1b[0m', '\n');
                }
            });
        } else {
            // eslint-disable-next-line no-console
            console.error('\n', '\x1b[31m', 'e2e teardown failed - no available token', '\x1b[0m', '\n');
        }
    })
    .page`${url}`;


test('[Initialise]', async () => {
    log('Create Organisation');
    await click(byId('jsSignup'));
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train'); // visit the url
    await setText(byId('email'), email); // visit the url
    await setText(byId('password'), password); // visit the url
    await click(byId('signup-btn'));
    await setText('[name="orgName"]', 'Bullet Train Ltd');
    await click('#create-org-btn');
    await waitForElementVisible(byId('project-select-page'));

    log('Create Project');
    await click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await click(byId('create-project-btn'));
    await waitForElementVisible((byId('features-page')));

    log('Hide disabled flags');
    await click('#project-settings-link');
    await click(byId('js-hide-disabled-flags'));
    await setText(byId('js-project-name'), 'My Test Project');
    await click(byId('js-confirm'));

}).after(async (t) => {
    console.log('Start of Initialise Requests');
    await logResults(logger.requests);
    console.log('Start of Initialise Requests');
});
