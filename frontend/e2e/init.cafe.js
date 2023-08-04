import fetch from 'node-fetch';
import Project from '../common/project';
import {
    deleteFeature,
    deleteSegment,
    getLogger,
    gotoFeatures,
    gotoSegments,
    logout,
    logResults,
} from './helpers.cafe';
import environmentTest from './tests/environment-test';
import inviteTest from './tests/invite-test';
import projectTest from './tests/project-test';
import segmentTest from './tests/segment-test';
import initialiseTests from './tests/initialise-tests';

require('dotenv').config();

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
    console.log("Init")
    // await initialiseTests()
    // await logout()
    // await environmentTest()
    // await logout()
    // await projectTest()
    // await logout()
    // await segmentTest()
    // await logout()
    // await inviteTest()
}).after(async (t) => {
    console.log('Start of Initialise Requests');
    await logResults(logger.requests, t);
    console.log('End of Initialise Requests');
});
