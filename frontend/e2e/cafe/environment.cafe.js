import { byId, click, log, login, setText, waitForElementVisible } from '../helpers.cafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';

fixture`Environment Tests`
    .page`http://localhost:3000/`;
test.clientScripts({
    content: `
        window.addEventListener('error', function (e) {
            console.error(e.message); 
        });`
})(`Skip error but log it`, async t => {
    console.log(await t.getBrowserConsoleMessages());
});
test('Submit a Form', async () => {
    log('Login', 'Environment Test');
    await login(email, password);
    await click('#project-select-0');
    log('Create environment', 'Environment Test');
    await click('#create-env-link');
    await setText('[name="envName"]', 'Staging');
    await click('#create-env-btn');
    await waitForElementVisible(byId('switch-environment-staging-active'));
    log('Edit Environment', 'Environment Test');
    await click('#env-settings-link');
    await setText("[name='env-name']", 'Internal');
    await click('#save-env-btn');
    log('Delete environment', 'Environment Test');
    await click('#delete-env-btn');
    await setText("[name='confirm-env-name']", 'Internal');
    await click('#confirm-delete-env-btn');
    await waitForElementVisible(byId('features-page'));
});
