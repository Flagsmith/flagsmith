import { test } from '@playwright/test';
import {
    assertNumberOfVersions,
    byId,
    click,
    compareVersion,
    createFeature,
    createOrganisationAndProject,
    createRemoteConfig,
    editRemoteConfig,
    log,
    login,
    waitForElementVisible
} from '../helpers/helpers';
import { E2E_USER, PASSWORD } from '../config';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../../common/project';

test('@oss Feature versioning test', async ({ page }) => {
    await flagsmith.init({ fetch, environmentID: Project.flagsmith, api: Project.flagsmithClientAPI });
    const hasFeature = flagsmith.hasFeature('feature_versioning');
    
    log('Login');
    await login(page, E2E_USER, PASSWORD);
    
    if (!hasFeature) {
        log('Skipping version test, feature not enabled.');
        return;
    }

    await createOrganisationAndProject(page, 'Flagsmith Versioning Org', 'Flagsmith Versioning Project');
    await waitForElementVisible(page, byId('features-page'));
    await click(page, '#env-settings-link');
    await click(page, byId('enable-versioning'));
    await click(page, '#confirm-btn-yes');
    await waitForElementVisible(page, byId('feature-versioning-enabled'));

    log('Create feature 1');
    await createRemoteConfig(page, 0, 'a', 'small');
    log('Edit feature 1');
    await editRemoteConfig(page, 0, 'medium');

    log('Create feature 2');
    await createRemoteConfig(page, 1, 'b', 'small', null, null, [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ]);
    log('Edit feature 2');
    await editRemoteConfig(page, 1, 'small', false, [
        { value: 'medium', weight: 0 },
        { value: 'big', weight: 100 },
    ]);

    log('Create feature 3');
    await createFeature(page, 2, 'c', false);
    log('Edit feature 3');
    await editRemoteConfig(page, 2, '', true);

    log('Edit feature 3');
    await assertNumberOfVersions(page, 0, 2);
    await assertNumberOfVersions(page, 1, 2);
    await assertNumberOfVersions(page, 2, 2);
    await compareVersion(page, 0, 0, null, true, true, 'small', 'medium');
    await compareVersion(page, 1, 0, null, true, true, 'small', 'small');
    await compareVersion(page, 2, 0, null, false, true, null, null);
});
