import { test, expect } from '../test-setup';
import { byId, getFlagsmith, log, createHelpers, LONG_TIMEOUT } from '../helpers';
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config';
import type { Page } from '@playwright/test';

// Regression tests for the multivariate option save flow: variants must
// never duplicate on repeated saves, deletes must apply, and labels/weights
// must survive a save under v2 feature versioning.

const openFeature = async (page: Page, name: string) => {
  const featureRow = page.locator('[data-test^="feature-item-"]').filter({
    has: page.locator(`span:text-is("${name}")`),
  }).first();
  await featureRow.waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
  await featureRow.dispatchEvent('click');
  await page.locator(byId('update-feature-btn')).first().waitFor({ state: 'visible', timeout: LONG_TIMEOUT });
};

const variantCards = (page: Page) => page.locator('#create-feature-modal .variant-card');

test.describe('Multivariate Options', () => {
  test('Repeated saves keep the variant set stable @oss', async ({ page }) => {
    const {
      closeModal,
      createRemoteConfig,
      editRemoteConfig,
      editVariantLabel,
      gotoFeatures,
      gotoProject,
      login,
      waitForElementNotExist,
    } = createHelpers(page);

    log('Login');
    await login(E2E_USER, PASSWORD);
    await gotoProject(E2E_TEST_PROJECT);

    log('Create multivariate flag');
    await createRemoteConfig({ name: 'mv_repeat_save', value: 'ctrl_value', mvs: [
      { value: 'va', weight: 0 },
      { value: 'vb', weight: 0 },
    ]});

    log('First save: label-only edit');
    await editVariantLabel('mv_repeat_save', 0, 'first_variant');

    log('Second save: value and weights, without structural changes');
    await editRemoteConfig('mv_repeat_save', 'ctrl_value2', false, [
      { value: 'va', weight: 30 },
      { value: 'vb', weight: 20 },
    ]);

    log('Variant set is unchanged after both saves');
    await gotoFeatures();
    await openFeature(page, 'mv_repeat_save');
    await expect(variantCards(page)).toHaveCount(2);
    await expect(page.locator(byId('featureVariationKey0'))).toHaveText('first_variant');
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');
  });

  test('Variants can be added and removed in a single save @oss', async ({ page }) => {
    const {
      click,
      closeModal,
      createRemoteConfig,
      gotoFeatures,
      gotoProject,
      login,
      setText,
      waitForElementNotExist,
      waitForToast,
    } = createHelpers(page);

    log('Login');
    await login(E2E_USER, PASSWORD);
    await gotoProject(E2E_TEST_PROJECT);

    log('Create multivariate flag');
    await createRemoteConfig({ name: 'mv_add_remove', value: 'root_val', mvs: [
      { value: 'keep', weight: 0 },
      { value: 'drop', weight: 0 },
    ]});

    log('Remove one variant and add another in the same edit');
    await openFeature(page, 'mv_add_remove');
    await page.locator('#create-feature-modal #delete-multivariate').nth(1).click();
    await click('#confirm-btn-yes');
    await expect(variantCards(page)).toHaveCount(1);
    await click(byId('add-variation'));
    await page.waitForTimeout(200);
    await setText(byId('featureVariationValue1'), 'added');
    await page.waitForTimeout(500);
    await click(byId('update-feature-btn'));
    await waitForToast();
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');

    log('Saved set is exactly the kept and added variants');
    await gotoFeatures();
    await openFeature(page, 'mv_add_remove');
    await expect(variantCards(page)).toHaveCount(2);
    await expect(page.locator(byId('featureVariationWeightkeep'))).toBeVisible();
    await expect(page.locator(byId('featureVariationWeightadded'))).toBeVisible();
    await expect(page.locator(byId('featureVariationWeightdrop'))).toHaveCount(0);
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');
  });

  test('Variant labels and weights persist under v2 feature versioning @oss', async ({ page }) => {
    const {
      click,
      closeModal,
      createOrganisationAndProject,
      createRemoteConfig,
      gotoFeatures,
      login,
      setText,
      waitForElementNotExist,
      waitForElementVisible,
      waitForToast,
      waitForToastsToClear,
    } = createHelpers(page);
    const flagsmith = await getFlagsmith();
    const hasFeature = flagsmith.hasFeature('feature_versioning');

    log('Login');
    await login(E2E_USER, PASSWORD);

    if (!hasFeature) {
      log('Skipping mv versioning test, feature not enabled.');
      test.skip();
      return;
    }

    await createOrganisationAndProject('Mv Options Versioning Org', 'Mv Options Versioning Project');
    await waitForElementVisible(byId('features-page'));
    await click('#env-settings-link');
    await click(byId('enable-versioning'));
    await click('#confirm-btn-yes');
    // Feature versioning takes up to a minute to enable on the backend
    await waitForElementVisible(byId('feature-versioning-enabled'));
    await waitForElementVisible('.toast-message');
    await waitForToastsToClear();

    log('Create multivariate flag in versioned environment');
    await createRemoteConfig({ name: 'mv_v2_flag', value: 'root_val', mvs: [
      { value: 'one', weight: 100 },
      { value: 'two', weight: 0 },
    ]});
    // Short delay between synchronising mv options and the next edit
    await page.waitForTimeout(1000);

    log('Edit label, flip weights and add a variant in one save');
    await gotoFeatures();
    await openFeature(page, 'mv_v2_flag');
    await click(byId('featureVariationKeyEdit0'));
    await setText(byId('featureVariationKeyInput0'), 'primary');
    await click(byId('featureVariationKeySave0'));
    await expect(page.locator(byId('featureVariationKey0'))).toHaveText('primary');
    for (const { value, weight } of [
      { value: 'one', weight: 0 },
      { value: 'two', weight: 100 },
    ]) {
      const input = page.locator(byId(`featureVariationWeight${value}`));
      await input.clear();
      await input.fill(`${weight}`);
      await input.blur();
      await page.waitForTimeout(200);
    }
    await click(byId('add-variation'));
    await page.waitForTimeout(200);
    await setText(byId('featureVariationValue2'), 'three');
    await page.waitForTimeout(500);
    await click(byId('update-feature-btn'));
    await waitForToast();
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');

    log('Label, weights and the new variant survived the versioned save');
    await gotoFeatures();
    await openFeature(page, 'mv_v2_flag');
    await expect(variantCards(page)).toHaveCount(3);
    await expect(page.locator(byId('featureVariationKey0'))).toHaveText('primary');
    await expect(page.locator(byId('featureVariationWeighttwo'))).toHaveValue('100');
    await expect(page.locator(byId('featureVariationWeightthree'))).toBeVisible();
    await closeModal();
    await waitForElementNotExist('#create-feature-modal');
  });
});
