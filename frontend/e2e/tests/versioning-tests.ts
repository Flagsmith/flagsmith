import {
    assertNumberOfVersions,
    byId,
    checkApiRequest,
    click,
    compareVersion,
    createFeature,
    createOrganisationAndProject,
    createRemoteConfig,
    editRemoteConfig,
    getFlagsmith,
    log,
    login,
    parseTryItResults,
    toggleFeature,
    waitForElementVisible,
} from '../helpers.cafe';
import { t } from 'testcafe';
import { E2E_USER, PASSWORD } from '../config';

// Request logger to verify versioned toggle uses the versions API endpoint
// Versioned: POST /environments/{envId}/features/{featureId}/versions/
const versionApiLogger = checkApiRequest(/\/features\/\d+\/versions\/$/, 'post')

export default async () => {
    const flagsmith = await getFlagsmith()
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

    log('Assert version counts')
    await assertNumberOfVersions(0, 2)
    await assertNumberOfVersions(1, 2)
    await assertNumberOfVersions(2, 2)
    await compareVersion(0,0,null,true,true, 'small','medium')
    await compareVersion(1,0,null,true,true, 'small','small')
    await compareVersion(2,0,null,false,true, null,null)

    // ===================================================================================
    // Test: Row toggle in versioned environment
    // This tests that toggling a feature via the row switch works when Feature Versioning
    // is enabled. The toggle must use the versioning API instead of the regular PUT.
    // We reuse the existing versioned environment from the tests above.
    // Note: Feature 'c' is currently ON after editRemoteConfig(2,'',true) above.
    // ===================================================================================
    log('Test row toggle in versioned environment')

    // Clear any previous requests from the logger
    await t.addRequestHooks(versionApiLogger)
    versionApiLogger.clear()

    // Feature 'c' (index 2) is currently ON - toggle it OFF
    log('Toggle feature OFF via row switch (versioned env)')
    await toggleFeature(2, false)

    // Verify: Versioned API endpoint was called (POST /features/{id}/versions/)
    log('Verify versioned API endpoint was called')
    await t.expect(versionApiLogger.requests.length).gte(1, 'Expected versioned API to be called')

    // Verify: Switch shows OFF state on features list
    await waitForElementVisible(byId('feature-switch-2-off'))

    // Verify: API returns correct state (feature disabled)
    log('Verify API returns disabled state')
    await t.wait(500)
    await click('#try-it-btn')
    await t.wait(500)
    let json = await parseTryItResults()
    await t.expect(json.c.enabled).eql(false)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle OFF persisted')
    await t.eval(() => location.reload())
    await waitForElementVisible(byId('features-page'))
    await waitForElementVisible(byId('feature-switch-2-off'))

    // Clear logger before second toggle
    versionApiLogger.clear()

    // Toggle feature 'c' back ON using row switch
    log('Toggle feature ON via row switch (versioned env)')
    await toggleFeature(2, true)

    // Verify: Versioned API endpoint was called again
    log('Verify versioned API endpoint was called for toggle ON')
    await t.expect(versionApiLogger.requests.length).gte(1, 'Expected versioned API to be called for toggle ON')

    // Verify: Switch shows ON state on features list
    await waitForElementVisible(byId('feature-switch-2-on'))

    // Verify: API returns correct state (feature enabled)
    log('Verify API returns enabled state')
    await t.wait(500)
    await click('#try-it-btn')
    await t.wait(500)
    json = await parseTryItResults()
    await t.expect(json.c.enabled).eql(true)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle ON persisted')
    await t.eval(() => location.reload())
    await waitForElementVisible(byId('features-page'))
    await waitForElementVisible(byId('feature-switch-2-on'))

    log('Versioned toggle test passed')
}
