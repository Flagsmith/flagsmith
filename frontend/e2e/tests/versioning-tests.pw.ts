import { test, expect } from '../test-setup';
import {
    byId,
    getFlagsmith,
    log,
    createHelpers,
} from '../helpers';
import { E2E_USER, PASSWORD } from '../config';

test('Versioning tests - Create, edit, and compare feature versions @oss', async ({ page }) => {
    const {
        assertNumberOfVersions,
        click,
        compareVersion,
        createFeature,
        createOrganisationAndProject,
        createRemoteConfig,
        editRemoteConfig,
        login,
        parseTryItResults,
        toggleFeature,
        waitForElementVisible,
        waitForFeatureSwitch,
    } = createHelpers(page)
    const flagsmith = await getFlagsmith()
    const hasFeature = flagsmith.hasFeature("feature_versioning")

    log('Login')
    await login(E2E_USER, PASSWORD)

    if(!hasFeature) {
        log("Skipping version test, feature not enabled.")
        test.skip()
        return
    }

    await createOrganisationAndProject('Flagsmith Versioning Org', 'Flagsmith Versioning Project')
    await waitForElementVisible(byId('features-page'))
    await click('#env-settings-link')
    await click(byId('enable-versioning'))
    await click('#confirm-btn-yes')
    // Feature versioning takes up to a minute to enable on the backend
    await waitForElementVisible(byId('feature-versioning-enabled'))

    log('Create feature 1')
    await createRemoteConfig({ name: 'a', value: 'small' })
    log('Edit feature 1')
    await editRemoteConfig('a', 'medium')

    log('Create feature 2')
    await createRemoteConfig({ name: 'b', value: 'small', mvs: [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ]})
    log('Edit feature 2')
    await editRemoteConfig('b', 'small', false, [
        { value: 'medium', weight: 0 },
        { value: 'big', weight: 100 },
    ])

    log('Create feature 3')
    await createFeature({ name: 'c', value: false })
    log('Edit feature 3')
    await editRemoteConfig('c', '', true)

    log('Assert version counts')
    await assertNumberOfVersions('a', 2)
    await assertNumberOfVersions('b', 2)
    await assertNumberOfVersions('c', 2)
    await compareVersion('a', 0, null, true, true, 'small', 'medium')
    await compareVersion('b', 0, null, true, true, 'small', 'small')
    await compareVersion('c', 0, null, false, true, null, null)

    // ===================================================================================
    // Test: Row toggle in versioned environment
    // This tests that toggling a feature via the row switch works when Feature Versioning
    // is enabled. The toggle must use the versioning API instead of the regular PUT.
    // We reuse the existing versioned environment from the tests above.
    // Note: Feature 'c' is currently ON after editRemoteConfig('c', '', true) above.
    // ===================================================================================
    log('Test row toggle in versioned environment')

    // Feature 'c' is currently ON - toggle it OFF
    log('Toggle feature OFF via row switch (versioned env)')
    await toggleFeature('c', false)

    // Verify: Switch shows OFF state on features list
    await waitForFeatureSwitch('c', 'off')

    // Verify: API returns correct state (feature disabled)
    log('Verify API returns disabled state')
    await click('#try-it-btn')
    let json = await parseTryItResults()
    expect(json.c.enabled).toBe(false)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle OFF persisted')
    await page.reload()
    await waitForElementVisible(byId('features-page'))
    await waitForFeatureSwitch('c', 'off')

    // Toggle feature 'c' back ON using row switch
    log('Toggle feature ON via row switch (versioned env)')
    await toggleFeature('c', true)

    // Verify: Switch shows ON state on features list
    await waitForFeatureSwitch('c', 'on')

    // Verify: API returns correct state (feature enabled)
    log('Verify API returns enabled state')
    // In versioned environments, changes may take MUCH longer to propagate to the edge API
    // Versioning requires backend processing that can take several seconds
    await page.waitForTimeout(10000)

    // Click "Try it" button and wait for network request to complete
    const responsePromise = page.waitForResponse(response =>
      response.url().includes('/flags/') && response.request().method() === 'GET'
    );
    await click('#try-it-btn')
    await responsePromise

    json = await parseTryItResults()
    expect(json.c.enabled).toBe(true)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle ON persisted')
    await page.reload()
    await waitForElementVisible(byId('features-page'));
    await waitForFeatureSwitch('c', 'on');

    log('Versioned toggle test passed');
})
