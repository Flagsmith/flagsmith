import { test, expect } from '../test-setup';
import { byId, createHelpers, getFlagsmith, log, visualSnapshot } from '../helpers';
import { E2E_SIGN_UP_USER, PASSWORD } from '../config';

// The single-page onboarding flow (onboarding_quickstart_flow) a new user lands
// on at /getting-started. Mirror of the legacy signup test's guard: this runs
// only when the flag is on, the legacy signup test runs only when it's off.
//
// Selectors are accessibility-first (roles / labels / text), not data-test ids:
// the header inputs expose aria-labels, the copy buttons and the flag switch
// carry accessible names, and the flags table is a labelled region.
test.describe('Onboarding', () => {
  test('New user connects via the single-page onboarding flow @oss', async ({
    page,
  }, testInfo) => {
    const { addErrorLogging, click, setText, waitForElementVisible } =
      createHelpers(page);
    const flagsmith = await getFlagsmith();

    test.skip(
      !flagsmith.hasFeature('onboarding_quickstart_flow'),
      'Onboarding flow is behind onboarding_quickstart_flow',
    );

    await addErrorLogging();

    // The flow renders once bootstrap settles (it shows a loader, then an error
    // heading on failure - so the welcome heading means "ready").
    const flowReady = async () =>
      page
        .getByRole('heading', { name: /Welcome/ })
        .waitFor({ state: 'visible', timeout: 30000 });

    // Sign up a fresh user; with the flag on, a getting-started user is routed
    // to /getting-started where the flow bootstraps the org / project / flag.
    log('Sign up');
    await page.goto('/');
    await click(byId('jsSignup'));
    await waitForElementVisible(byId('firstName'));
    await setText(byId('firstName'), 'Bullet');
    await setText(byId('lastName'), 'Train');
    await setText(byId('email'), E2E_SIGN_UP_USER);
    await setText(byId('password'), PASSWORD);
    await click(byId('signup-btn'));

    // Don't navigate manually - a goto here races the post-signup auth and gets
    // bounced to /?redirect=. The app redirects a getting-started user to the
    // flow itself once authenticated, so just wait for it to land there.
    log('Land on the onboarding flow');
    await page.waitForURL((url) => url.pathname === '/getting-started', {
      timeout: 30000,
    });
    await flowReady();
    await visualSnapshot(page, 'onboarding-flow', testInfo);

    // The verify terminal starts pre-connection: LISTENING, nothing ticked.
    await expect(page.getByText('LISTENING')).toBeVisible();
    await expect(page.getByText('Copy install command')).not.toContainText('✓');

    // Copying the install + wire snippets ticks the checklist (the visible
    // [✓] prefix is the done state).
    log('Copy snippets, checklist ticks');
    await page.getByRole('button', { name: 'Copy install command' }).click();
    await expect(page.getByText('Copy install command')).toContainText('✓');
    await page.getByRole('button', { name: 'Copy code snippet' }).click();
    await expect(page.getByText('Copy code snippet')).toContainText('✓');

    // The flags table is locked until the app connects, and there's no real
    // first evaluation in a test - so force the connected state via ?connected
    // (the stub seam for #7767). The badge flips to LIVE and the toggle unlocks.
    log('Force the connected state');
    await page.goto('/getting-started?connected');
    await flowReady();
    await expect(page.getByText('LIVE', { exact: true })).toBeVisible();

    // Now the Development toggle is enabled. Two switches on the page (theme +
    // flag), so scope to the flags region.
    log('Toggle the flag');
    const flagsTable = page.getByRole('region', { name: 'Your flags' });
    const flagSwitch = flagsTable.getByRole('switch');
    await flagSwitch.waitFor({ state: 'visible' });
    const wasChecked = (await flagSwitch.getAttribute('class'))?.includes(
      'switch-checked',
    );
    await flagSwitch.click();
    await expect(flagSwitch).toHaveClass(
      wasChecked ? /switch-unchecked/ : /switch-checked/,
    );

    // The Onboarding badge (attached in bootstrap) shows in the flags table.
    // Exact match: the header crumb also contains the word "Onboarding".
    await expect(flagsTable.getByText('Onboarding', { exact: true })).toBeVisible();

    // Rename the flag. Names are immutable, so this delete + recreates; the
    // Onboarding tag must survive (the recreate carries the old flag's tags).
    log('Rename the flag');
    const flagInput = page.getByLabel('Flag name');
    await flagInput.fill('renamed_demo_flag');
    await flagInput.press('Enter');

    // Wait for the rename to persist before reloading - it's a delete + recreate
    // (two requests), and reloading too early aborts them. The success toast
    // fires once both land.
    await expect(page.getByText('Flag name updated')).toBeVisible({
      timeout: 20000,
    });

    // Reload to prove the rename persisted server-side and the tag came with it
    // (bootstrap is idempotent and reuses the renamed flag on revisit).
    await page.reload();
    await flowReady();
    await expect(page.getByLabel('Flag name')).toHaveValue('renamed_demo_flag');
    await expect(
      page
        .getByRole('region', { name: 'Your flags' })
        .getByText('Onboarding', { exact: true }),
    ).toBeVisible();
    await visualSnapshot(page, 'onboarding-renamed', testInfo);
  });
});
