import { test, expect } from '../test-setup';
import { byId, createHelpers, getFlagsmith, log, visualSnapshot } from '../helpers';
import { E2E_SIGN_UP_USER, PASSWORD } from '../config';

// The single-page onboarding flow (onboarding_quickstart_flow), at
// /getting-started. Runs only when the flag is on (the legacy signup test runs
// when it's off).
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

    // Drive the verify console's real first-evaluation signal: Edge
    // reports to Core, which the page polls at onboarding-status/. Flip
    // firstEvaluated to simulate that landing (there's no real SDK eval here).
    let firstEvaluated = false;
    await page.route(/onboarding-status\//, (route) =>
      route.fulfill({
        json: {
          first_evaluated_at: firstEvaluated ? '2024-01-01T00:00:00Z' : null,
          first_evaluated_sdk_label: firstEvaluated ? 'flagsmith-js-sdk' : null,
        },
      }),
    );

    // The welcome heading means bootstrap settled (loader, then heading/error).
    const flowReady = async () =>
      page
        .getByRole('heading', { name: /Welcome/ })
        .waitFor({ state: 'visible', timeout: 30000 });

    // The console polls every few seconds, so LIVE lands shortly after the flip.
    const waitConnected = () =>
      expect(page.getByText('LIVE', { exact: true })).toBeVisible({
        timeout: 15000,
      });

    // The features page syncs the slideout state to the URL with
    // history.replace, which aborts a full navigation that is still in
    // flight - let the page settle and retry.
    const gotoOnboarding = async () => {
      for (let attempt = 0; ; attempt++) {
        try {
          await page.goto('/getting-started');
          return;
        } catch (e) {
          if (attempt >= 2) throw e;
          await page.waitForTimeout(1000);
        }
      }
    };

    log('Sign up');
    await page.goto('/');
    await click(byId('jsSignup'));
    await waitForElementVisible(byId('firstName'));
    await setText(byId('firstName'), 'Bullet');
    await setText(byId('lastName'), 'Train');
    await setText(byId('email'), E2E_SIGN_UP_USER);
    await setText(byId('password'), PASSWORD);
    await click(byId('signup-btn'));

    // Don't navigate manually - a goto races the post-signup auth and bounces to
    // /?redirect=. The app routes a getting-started user here itself, so just wait.
    log('Land on the onboarding flow');
    await page.waitForURL((url) => url.pathname === '/getting-started', {
      timeout: 30000,
    });
    await flowReady();
    await visualSnapshot(page, 'onboarding-flow', testInfo);

    await expect(page.getByText('LISTENING')).toBeVisible();
    await expect(page.getByText('Copy install command')).not.toContainText('✓');

    // Before the first evaluation, the next-quest cards are locked.
    await expect(
      page.getByText('Unlocks after your first evaluation'),
    ).toBeVisible();

    log('Copy snippets, checklist ticks');
    await page.getByRole('button', { name: 'Copy install command' }).click();
    await expect(page.getByText('Copy install command')).toContainText('✓');
    await page.getByRole('button', { name: 'Copy code snippet' }).click();
    await expect(page.getByText('Copy code snippet')).toContainText('✓');

    // The first evaluation lands; the console polls onboarding-status/ and
    // flips to LIVE on its own - no reload needed.
    log('First evaluation received, console flips to LIVE');
    firstEvaluated = true;
    await waitConnected();

    // The console names the SDK that reported the evaluation, from the mocked
    // first_evaluated_sdk_label above.
    await expect(page.getByText(/flagsmith-js-sdk/)).toBeVisible();

    // Two switches on the page (theme + flag), so scope to the flags region.
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
    const flagInput = page.getByLabel('Edit flag');
    await flagInput.fill('renamed_demo_flag');
    await flagInput.press('Enter');

    // Wait for the rename to persist before reloading - it's a delete + recreate,
    // and reloading too early aborts the requests. The toast fires once both land.
    await expect(page.getByText('Flag name updated')).toBeVisible({
      timeout: 20000,
    });

    // Reload to prove it persisted (bootstrap reuses the renamed flag).
    await page.reload();
    await flowReady();
    await expect(page.getByLabel('Edit flag')).toHaveValue('renamed_demo_flag');
    await expect(
      page
        .getByRole('region', { name: 'Your flags' })
        .getByText('Onboarding', { exact: true }),
    ).toBeVisible();
    // The reload dropped the connected latch, so wait for the console to flip
    // back before snapshotting: the badge state would otherwise race the first
    // poll and diff against the baseline.
    await waitConnected();
    await visualSnapshot(page, 'onboarding-renamed', testInfo);

    // The next-quest cards unlock once connected, each deep-linking to the
    // flag's real config (nothing faked).
    log('Next-quest cards link to the real config');
    await expect(
      page.getByRole('heading', { name: 'Choose your next quest' }),
    ).toBeVisible();

    await page.getByRole('button', { name: /Gradual rollout/ }).click();
    await expect(page).toHaveURL(
      /\/features\?feature=\d+&tab=segment-overrides/,
    );

    await gotoOnboarding();
    await flowReady();
    await waitConnected();
    await page.getByRole('button', { name: /Remote config/ }).click();
    await expect(page).toHaveURL(/\/features\?feature=\d+&tab=value/);

    await gotoOnboarding();
    await flowReady();
    await waitConnected();
    await page.getByRole('button', { name: /Experiment/ }).click();
    await expect(page).toHaveURL(/\/experiments$/);
  });
});
