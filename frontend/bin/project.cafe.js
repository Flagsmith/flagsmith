import { byId, click, getLogger, log, login, setText, waitForElementVisible } from '../e2e/helpers.cafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';
const logger = getLogger()

fixture`Project Tests`
    .page`http://localhost:3000/`
    .requestHooks(logger)

test('Project Test', async () => {
    log('Login', 'Project Test');
    await login(email, password);
    await click('#project-select-0');
    log('Edit Project', 'Project Test');
    await click('#project-settings-link');
    await setText("[name='proj-name']", 'Test Project');
    await click('#save-proj-btn');
    await waitForElementVisible(byId('switch-project-test project-active'));
}).after(async (t)=>{
    console.log("Start of Project Requests")
    console.log(JSON.stringify(logger.requests, null,2))
    console.log("End of Project Requests")
    console.log("Start of Project Errors")
    console.error(JSON.stringify((await t.getBrowserConsoleMessages()).error));
    console.log("End of Project Errors")
})

