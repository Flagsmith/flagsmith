// global-setup.ts
import { chromium, FullConfig } from '@playwright/test';
import {fork} from "child_process";
import fetch from 'node-fetch';
import {
    addSegmentOverride,
    assertTextContent,
    byId,
    click, closeModal,
    createFeature,
    createRemoteConfig, createSegment, createTrait,
    deleteFeature, deleteSegment, deleteTrait, getText, gotoFeature, gotoFeatures, gotoSegments, gotoTraits,
    log,
    setText, toggleFeature,
    waitForElementVisible
} from "./tests/helpers.e2e";
require('dotenv').config();
const Project = require("../common/project")
let server
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const quick = false;
async function globalSetup(config: FullConfig) {
    const token = process.env.E2E_TEST_TOKEN
        ? process.env.E2E_TEST_TOKEN : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`];

    await new Promise((resolve) => {
        process.env.PORT = "3000";
        server = fork('./api/index');
        server.on('message', () => {
            resolve(null);
        });
    });
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

    const url = `http://localhost:${process.env.PORT || 8080}/`;
    const browser = await chromium.launch({
        headless: !process.env.E2E_DEV
    })
    const page = await browser.newPage();

    await page.goto(url);
    log('Create Organisation');
    await click(byId('jsSignup'), page);
    await setText(byId('firstName'), 'Bullet', page); // visit the url
    await setText(byId('lastName'), 'Train', page); // visit the url
    await setText(byId('email'), email, page); // visit the url
    await setText(byId('password'), password, page); // visit the url
    await click(byId('signup-btn'), page);
    await setText('[name="orgName"]', 'Bullet Train Ltd', page);
    await click('#create-org-btn', page);
    await waitForElementVisible(byId('project-select-page'), page);

    log('Create Project');
    await click(byId('create-first-project-btn'), page);
    await setText(byId('projectName'), 'My Test Project', page);
    await click(byId('create-project-btn'), page);
    await waitForElementVisible((byId('features-page')), page);

    log('Hide disabled flags');
    await click('#project-settings-link', page);
    await click(byId('js-hide-disabled-flags'), page);
    await setText(byId('js-project-name'), 'My Test Project', page);
    await click(byId('js-confirm'), page);
    await click('#features-link', page);

    if(!quick) {
        log('Create Features');
        await createRemoteConfig(page, 0, 'header_size', 'big');
        await createRemoteConfig(page, 0, 'mv_flag', 'big', null, null, [
            { value: 'medium', weight: 100 },
            { value: 'small', weight: 0 },
        ]);
        await createFeature(page,1, 'header_enabled', false);
        //
        // log('Create Short Life Feature');
        await createFeature(page,3, 'short_life_feature', false);
        await deleteFeature(page,3, 'short_life_feature');
        log('Toggle Feature');
        await toggleFeature(0, true, page);
        log('Try it');
        await page.waitForTimeout(1500)
        await click('#try-it-btn', page)
        await page.waitForTimeout(1500)
        let text = await getText('#try-it-results', page);
        let json;
        try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
        if (json.header_size.value !== 'big') {
            throw "Expected header size big, got "  + json.header_size.value
        }
        if (json.mv_flag.value !== 'big') {
            throw "Expected mv flag big, got "  + json.mv_flag.value
        }
        if (!json.header_enabled.enabled) {
            throw "Expected header enabled"
        }
        log('Update feature');
        await click(byId('feature-item-1'),page);
        await setText(byId('featureValue'), '12',page);
        await click('#update-feature-btn', page);
        await assertTextContent(byId('feature-value-1'), '12', page);
        await page.keyboard.press('Escape');
        await closeModal(page);

        log('Try it again');
        await page.waitForTimeout(1500)
        await click('#try-it-btn', page)
        await page.waitForTimeout(1500)
        text = await getText('#try-it-results', page);
        try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
        if (json.header_size.value !== 12) {
            throw "Expected header size 12, got "  + json.header_size.value
        }

        log('Change feature value to boolean');
        await click(byId('feature-item-1'), page);
        await setText(byId('featureValue'), 'false', page);
        await click('#update-feature-btn', page);
        await assertTextContent(byId('feature-value-1'), 'false', page);
        await closeModal(page);

        log('Try it again 2');
        await page.waitForTimeout(1500)
        await click('#try-it-btn', page)
        await page.waitForTimeout(1500)
        text = await getText('#try-it-results', page);
        try { json = JSON.parse(text); } catch (e) { throw new Error('Try it results are not valid JSON'); }
        if (json.header_size.value !== false) {
            throw "Expected header size false, got "  + json.header_size.value
        }
        log('Switch environment');
        await click(byId('switch-environment-production'), page);

        log('Feature should be off under different environment');
        await waitForElementVisible(byId('switch-environment-production-active'), page);
        await waitForElementVisible(byId('feature-switch-0-off'), page);

        log('Clear down features');
        await deleteFeature(page,1, 'header_size');
        await deleteFeature(page, 0, 'header_enabled');

        await gotoSegments(page);

        await createSegment(page,0, '18_or_19', [
            // rule 2 =18 || =17
            {
                name: 'age',
                operator: 'EQUAL',
                value: 18,
                ors: [
                    {
                        name: 'age',
                        operator: 'EQUAL',
                        value: 17,
                    },
                ],
            },
            // rule 2 >17 or <10
            {
                name: 'age',
                operator: 'GREATER_THAN',
                value: 17,
                ors: [
                    {
                        name: 'age',
                        operator: 'LESS_THAN',
                        value: 10,
                    },
                ],
            },
            // rule 3 !=20
            {
                name: 'age',
                operator: 'NOT_EQUAL',
                value: 20,
            },
            // Rule 4 <= 18
            {
                name: 'age',
                operator: 'LESS_THAN_INCLUSIVE',
                value: 18,
            },
            // Rule 5 >= 18
            {
                name: 'age',
                operator: 'GREATER_THAN_INCLUSIVE',
                value: 18,
            },
        ]);



        log('Put user in medium');
        await gotoTraits(page);
        await createTrait(0, 'age', 18,page);
        await page.waitForTimeout(5000)
        await page.reload({waitUntil:'domcontentloaded'})
        await assertTextContent(byId('user-feature-value-0'), '"medium"',page);
        await gotoFeatures(page);
        await gotoFeature(0, page);

        log('Put user in small');
        await addSegmentOverride(page, 0, true, 0, [
            { value: 'medium', weight: 0 },
            { value: 'small', weight: 100 },

        ]);
        await click('#update-feature-segments-btn',page);
        await closeModal(page);
        await gotoTraits(page);
        await page.waitForTimeout(5000)
        await page.reload({waitUntil:'domcontentloaded'})
        await assertTextContent(byId('user-feature-value-0'), '"small"',page);

        // log('Check user now belongs to segment');
        await assertTextContent(byId('segment-0-name'), '18_or_19',page);

        // log('Delete segment trait for user');
        await deleteTrait(page,0);


        log('Set user MV override');
        await click(byId('user-feature-0'),page);
        await click(byId('select-variation-medium'),page);
        await click(byId('update-feature-btn'),page);
        await assertTextContent(byId('user-feature-value-0'), '"medium"',page);

        log('Delete segment');
        await gotoSegments(page);
        await deleteSegment(0, '18_or_19',page);
        await gotoFeatures(page);
        await deleteFeature(page, 0, 'mv_flag');
    }

}

export default globalSetup
