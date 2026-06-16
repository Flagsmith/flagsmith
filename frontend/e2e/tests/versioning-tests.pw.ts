import { test, expect } from '../test-setup';
import {
    byId,
    getFlagsmith,
    log,
    createHelpers,
    visualSnapshot,
} from '../helpers';
import { E2E_USER, PASSWORD } from '../config';

test('Versioning tests - Create, edit, and compare feature versions @oss', async ({ page }, testInfo) => {
    const {
        assertNumberOfVersions,
        click,
        closeModal,
        compareVersion,
        createFeature,
        createOrganisationAndProject,
        createRemoteConfig,
        editRemoteConfig,
        gotoFeature,
        gotoFeatures,
        login,
        setText,
        toggleFeature,
        tryItExpect,
        waitForElementNotExist,
        waitForElementVisible,
        waitForFeatureSwitch,
        waitForToast,
        waitForToastsToClear,
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
    await waitForElementVisible('.toast-message')
    await waitForToastsToClear()

    await visualSnapshot(page, 'versioning-enabled', testInfo)

    log('Create feature 1')
    await createRemoteConfig({ name: 'a', value: 'small' })
    log('Edit feature 1')
    await editRemoteConfig('a', 'medium')

    log('Create feature 2')
    await createRemoteConfig({ name: 'b', value: 'small', mvs: [
        { value: 'medium', weight: 100 },
        { value: 'big', weight: 0 },
    ]})
    // Short delay between synchronising mv options and feature creation
    await page.waitForTimeout(1000)
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
    // Test: Multivariate option edits in a versioned environment
    // A label edit plus a structural change (new variant) in a single save must
    // survive a reopen — the versioned save consumes option ids positionally
    // from the multivariate save, so this pins that contract under v2.
    // ===================================================================================
    log('Edit variant label and add a variant in one save (versioned env)')
    await gotoFeatures()
    await gotoFeature('b')
    await click(byId('featureVariationKeyEdit0'))
    await setText(byId('featureVariationKeyInput0'), 'primary')
    await click(byId('featureVariationKeySave0'))
    await expect(page.locator(byId('featureVariationKey0'))).toHaveText('primary')
    await click(byId('add-variation'))
    await page.waitForTimeout(200)
    await setText(byId('featureVariationValue2'), 'huge')
    await page.waitForTimeout(500)
    await click(byId('update-feature-btn'))
    await waitForToast()
    await closeModal()
    await waitForElementNotExist('#create-feature-modal')

    log('Label and new variant survived the versioned save')
    await gotoFeatures()
    await gotoFeature('b')
    await expect(page.locator('#create-feature-modal .variant-card')).toHaveCount(3)
    await expect(page.locator(byId('featureVariationKey0'))).toHaveText('primary')
    await expect(page.locator(byId('featureVariationWeightbig'))).toHaveValue('100')
    await expect(page.locator(byId('featureVariationWeighthuge'))).toBeVisible()
    await closeModal()
    await waitForElementNotExist('#create-feature-modal')

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
    // Versioned environments have slower edge API propagation, allow more retries
    log('Verify API returns disabled state')
    await tryItExpect('c', 'enabled', false, 20)

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
    // Versioned environments have slower edge API propagation, allow more retries
    log('Verify API returns enabled state')
    await tryItExpect('c', 'enabled', true, 20)

    // Refresh page to verify state was persisted to backend
    log('Refresh page to verify toggle ON persisted')
    await page.reload()
    await waitForElementVisible(byId('features-page'));
    await waitForFeatureSwitch('c', 'on');

    log('Versioned toggle test passed');
})
