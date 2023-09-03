import {
    byId,
    click,
    log,
    setText,
    waitForElementVisible,
} from '../helpers.cafe';

const email = 'nightwatch@solidstategroup.com';
const password = 'str0ngp4ssw0rd!';

export default async function() {
    log('Create Organisation');
    await click(byId('jsSignup'));
    await setText(byId('firstName'), 'Bullet'); // visit the url
    await setText(byId('lastName'), 'Train'); // visit the url
    await setText(byId('email'), email + '.io'); // visit the url
    await setText(byId('password'), password); // visit the url
    await click(byId('signup-btn'));
    await setText('[name="orgName"]', 'Bullet Train Ltd 0');
    await click('#create-org-btn');
    await waitForElementVisible(byId('project-select-page'));

    log('Create Project');
    await click(byId('create-first-project-btn'));
    await setText(byId('projectName'), 'My Test Project');
    await click(byId('create-project-btn'));
    await waitForElementVisible((byId('features-page')));

    log('Hide disabled flags');
    await click('#project-settings-link');
    await click(byId('js-sdk-settings'));
    await click(byId('js-hide-disabled-flags'));
    await setText(byId('js-project-name'), 'My Test Project');
    await click(byId('js-confirm'));

}
