import { byId, click, log, login, setText, waitForElementVisible } from '../helpers.cafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
export default async function() {
    log('Login', 'Project Test');
    await login(email, password);
    await click('#project-select-0');
    log('Edit Project', 'Project Test');
    await click('#project-settings-link');
    await setText("[name='proj-name']", 'Test Project');
    await click('#save-proj-btn');
    await waitForElementVisible(byId('switch-project-test-project'));

}
