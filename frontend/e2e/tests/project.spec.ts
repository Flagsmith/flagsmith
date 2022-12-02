import {test, expect} from '@playwright/test';
import {byId, click, log, login, setText, waitForElementVisible} from "./helpers.e2e";
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;

test('Project', async ({page}) => {
    await page.goto(url);
    log('Login', 'Project Test');
    await login(email, password,page);
    await click('#project-select-0',page);
    log('Edit Project', 'Project Test');
    await click('#project-settings-link',page);
    await setText("[name='proj-name']", 'Test Project',page);
    await click('#save-proj-btn',page);
    await waitForElementVisible(byId('switch-project-test project-active'),page);
});
