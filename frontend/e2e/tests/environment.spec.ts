import {test, expect} from '@playwright/test';
import {byId, click, log, login, setText, waitForElementNotExist, waitForElementVisible} from "./helpers.e2e";
const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const url = `http://localhost:${process.env.PORT || 8080}/`;

test('Environment', async ({page}) => {
    await page.goto(url);
    log('Login', 'Environment Test');
    await login(email, password,page);
    await click('#project-select-0',page);
    log('Create environment', 'Environment Test');
    await click('#create-env-link',page);
    await setText('[name="envName"]', 'Staging',page);
    await click('#create-env-btn',page);
    await waitForElementVisible(byId('switch-environment-staging-active'),page);
    log('Edit Environment', 'Environment Test');
    await click('#env-settings-link',page);
    await setText("[name='env-name']", 'Internal',page);
    await click('#save-env-btn',page);
    await waitForElementVisible('.toast-message',page);
    log('Delete environment', 'Environment Test');
    await click('#delete-env-btn',page);
    await setText("[name='confirm-env-name']", 'Internal',page);
    await click('#confirm-delete-env-btn',page);
    await waitForElementVisible(byId('features-page'),page);
});
