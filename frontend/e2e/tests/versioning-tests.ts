import {
    assertTextContent,
    byId,
    click,
    createFeature, createOrganisationAndProject,
    createRemoteConfig, editRemoteConfig,
    gotoFeatures, goToUser,
    log,
    login,
    setText, waitAndRefresh,
    waitForElementVisible,
} from '../helpers.cafe';
import { E2E_USER, PASSWORD } from '../config';
import fetch from 'node-fetch'
import flagsmith from 'flagsmith/isomorphic';
import Project from '../../common/project';
export default async () => {
    await flagsmith.init({fetch,environmentID:Project.flagsmith,api:Project.flagsmithClientAPI})
    const hasFeature = flagsmith.hasFeature("feature_versioning")
    if(!hasFeature) {
        console.log("Skipping version test, feature not enabled.")
        return
    }

    log('Login')
    await login(E2E_USER, PASSWORD)
    await createOrganisationAndProject('Flagsmith Versioning Org', 'Flagsmith Versioning Project')
    await waitForElementVisible(byId('features-page'))
    await click('#env-settings-link')
    await click(byId('enable-versioning'))
    await click('#confirm-toggle-feature-btn')
    await waitAndRefresh()

    log('Create feature 1')
    await createRemoteConfig(0, 'header_size', 'small')
    log('Edit feature 1')
    await editRemoteConfig(0,'medium')

    log('Create feature 2')
    await createRemoteConfig(1, 'mv_flag', 'small', null, null, [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ])
    log('Edit feature 2')
    await editRemoteConfig(1,'small',false,[
        { value: 'medium', weight: 0 },
        { value: 'big', weight: 100 },
    ])

    log('Create feature 3')
    await createFeature(2, 'header_enabled', false)
    log('Edit feature 3')
    await editRemoteConfig(2,'',true)

}
