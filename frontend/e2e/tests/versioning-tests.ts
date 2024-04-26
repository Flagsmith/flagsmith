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
    waitAndRefresh,
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

    log('Create feature 1')
    await createRemoteConfig(0, 'a', 'small')
    log('Edit feature 1')
    await editRemoteConfig(0,'medium')

    log('Create feature 2')
    await createRemoteConfig(1, 'b', 'small', null, null, [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ])
    log('Edit feature 2')
    await editRemoteConfig(1,'small',false,[
        { value: 'medium', weight: 0 },
        { value: 'big', weight: 100 },
    ])

    log('Create feature 3')
    await createFeature(2, 'c', false)
    log('Edit feature 3')
    await editRemoteConfig(2,'',true)

    log('Edit feature 3')
    await assertNumberOfVersions(0, 2)
    await assertNumberOfVersions(1, 2)
    await assertNumberOfVersions(2, 2)
    await compareVersion(0,0,null,true,true, 'small','medium')
    await compareVersion(1,0,null,true,true, 'small','small')
    await compareVersion(2,0,null,false,true, null,null)
}
