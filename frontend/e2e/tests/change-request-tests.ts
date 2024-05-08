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
    login, refreshUntilElementVisible,
    waitForElementVisible
} from "../helpers.cafe";
import { E2E_USER, PASSWORD } from '../config';
import fetch from 'node-fetch';
import flagsmith from 'flagsmith/isomorphic';
import Project from '../../common/project';

export default async () => {
    await flagsmith.init({fetch,environmentID:Project.flagsmith,api:Project.flagsmithClientAPI})
    const hasFeature = flagsmith.hasFeature("feature_versioning")
    log('Login')
    await login(E2E_USER, PASSWORD)
    if(!hasFeature) {
        log("Skipping version test, feature not enabled.")
        return
    }

    await createOrganisationAndProject('Flagsmith Versioning Org', 'Flagsmith Versioning Project')
    await waitForElementVisible(byId('features-page'))
    await click('#env-settings-link')
    await click(byId('enable-versioning'))
    await click('#confirm-btn-yes')
    await waitForElementVisible(byId('feature-versioning-enabled'))

    await click(byId('enable-change-requests'))
    log('Create feature 1')
    await createRemoteConfig(0, 'a', 'small')
    log('Edit feature 1')
    await editRemoteConfig(0,'medium', false, [], true)

}
