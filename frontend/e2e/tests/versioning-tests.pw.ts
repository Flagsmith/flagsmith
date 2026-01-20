import { test, expect } from '../test-setup';
import {
    assertNumberOfVersions,
    byId,
    compareVersion,
    createFeature,
    createOrganisationAndProject,
    createRemoteConfig,
    editRemoteConfig,
    getFlagsmith,
    log,
    parseTryItResults,
    toggleFeature,
    createHelpers,
} from '../helpers.playwright';
import { E2E_USER, PASSWORD } from '../config';

test('Versioning tests - Create, edit, and compare feature versions @oss', async ({ page }) => {
    const helpers = createHelpers(page)
    const flagsmith = await getFlagsmith()
    const hasFeature = flagsmith.hasFeature("feature_versioning")

    log('Login')
    await helpers.login(E2E_USER, PASSWORD)

    if(!hasFeature) {
        log("Skipping version test, feature not enabled.")
        test.skip()
        return
    }

    await createOrganisationAndProject(page, 'Flagsmith Versioning Org', 'Flagsmith Versioning Project')
    await helpers.waitForElementVisible(byId('features-page'))
    await helpers.click('#env-settings-link')
    await helpers.click(byId('enable-versioning'))
    await helpers.click('#confirm-btn-yes')
    // Feature versioning takes up to a minute to enable on the backend
    await page.locator(byId('feature-versioning-enabled')).waitFor({ state: 'visible', timeout: 70000 })

    log('Create feature 1')
    await createRemoteConfig(page, 0, 'a', 'small')
    log('Edit feature 1')
    await editRemoteConfig(page, 0,'medium')

    log('Create feature 2')
    await createRemoteConfig(page, 1, 'b', 'small', null, null, [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ])
    log('Edit feature 2')
    await editRemoteConfig(page, 1,'small',false,[
        { value: 'medium', weight: 0 },
        { value: 'big', weight: 100 },
    ])

    log('Create feature 3')
    await createFeature(page, 2, 'c', false)
    log('Edit feature 3')
    await editRemoteConfig(page, 2,'',true)

    log('Assert version counts')
    await assertNumberOfVersions(page, 0, 2)
    await assertNumberOfVersions(page, 1, 2)
    await assertNumberOfVersions(page, 2, 2)
    await compareVersion(page, 0,0,null,true,true, 'small','medium')
    await compareVersion(page, 1,0,null,true,true, 'small','small')
    await compareVersion(page, 2,0,null,false,true, null,null)

    // ===================================================================================
    // Test: Row toggle in versioned environment
    // This tests that toggling a feature via the row switch works when Feature Versioning
    // is enabled. The toggle must use the versioning API instead of the regular PUT.
    // We reuse the existing versioned environment from the tests above.
    // Note: Feature 'c' is currently ON after editRemoteConfig(page, 2,'',true) above.
    // ===================================================================================
    log('Test row toggle in versioned environment')

    // Feature 'c' (index 2) is currently ON - toggle it OFF
    log('Toggle feature OFF via row switch (versioned env)')
    await toggleFeature(page, 2, false)

    // Verify: Switch shows OFF state on features list
    await helpers.waitForElementVisible(byId('feature-switch-2-off'))

    // Verify: API returns correct state (feature disabled)
    log('Verify API returns disabled state')
    await page.waitForTimeout(500)
    await helpers.click('#try-it-btn')
    await page.waitForTimeout(500)
    let json = await parseTryItResults(page)
    expect(json.c.enabled).toBe(false)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle OFF persisted')
    await page.reload()
    await helpers.waitForElementVisible(byId('features-page'))
    await helpers.waitForElementVisible(byId('feature-switch-2-off'))

    // Toggle feature 'c' back ON using row switch
    log('Toggle feature ON via row switch (versioned env)')
    await toggleFeature(page, 2, true)

    // Verify: Switch shows ON state on features list
    await helpers.waitForElementVisible(byId('feature-switch-2-on'))

    // Verify: API returns correct state (feature enabled)
    log('Verify API returns enabled state')
    // In versioned environments, changes may take MUCH longer to propagate to the edge API
    // Versioning requires backend processing that can take several seconds
    await page.waitForTimeout(10000)

    // Click "Try it" button and wait for network request to complete
    const responsePromise = page.waitForResponse(response =>
      response.url().includes('/flags/') && response.request().method() === 'GET'
    );
    await helpers.click('#try-it-btn')
    await responsePromise

    // Additional wait for UI to update with results
    await page.waitForTimeout(1000)
    json = await parseTryItResults(page)
    expect(json.c.enabled).toBe(true)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle ON persisted')
    await page.reload()
    await helpers.waitForElementVisible(byId('features-page'));
    await helpers.waitForElementVisible(byId('feature-switch-2-on'));

    log('Versioned toggle test passed');
})