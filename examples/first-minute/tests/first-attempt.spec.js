import { expect, test } from '@playwright/test';

async function interceptSdk(context) {
    const events = [];
    await context.route('**/api/v1/identities/**', (route) =>
        route.fulfill({
            json: {
                flags: [
                    {
                        feature: { id: 1, name: 'triage_guide' },
                        enabled: true,
                        feature_state_value: 'guided',
                        variant: 'guided',
                        metadata: { experiment: { id: 1, name: 'Test', in_experiment: true } },
                    },
                ],
                traits: [],
            },
        }),
    );
    await context.route('**/api/v1/events', async (route) => {
        events.push(...route.request().postDataJSON().events);
        await route.fulfill({ status: 202, body: '' });
    });
    return events;
}

for (const correct of [false, true]) {
    test(`two tabs share one exposure and one ${correct ? 'correct' : 'incorrect'} first answer`, async ({
        context,
        page,
    }) => {
        const events = await interceptSdk(context);
        const second = await context.newPage();
        const tabs = [page, second];
        await Promise.all(tabs.map((tab) => tab.goto('/')));
        for (const tab of tabs) await expect(tab.locator('#mode')).toHaveText('Connected to Flagsmith');
        await Promise.all(tabs.map((tab) => tab.locator('#start').click()));
        for (const tab of tabs) await expect(tab.locator('#desk')).toBeVisible();

        await page.locator(`input[value="${correct ? 'pool' : 'traffic'}"]`).check();
        await second.locator('input[value=pool]').check();
        if (correct) {
            await Promise.all(tabs.map((tab) => tab.locator('#form').evaluate((form) => form.requestSubmit())));
        } else {
            await page.locator('#submit').click();
        }
        const verdict = correct ? 'Root cause found.' : 'Look at the connection queue.';
        for (const tab of tabs) await expect(tab.locator('#verdict')).toHaveText(verdict);
        await second.reload();
        await expect(second.locator('#verdict')).toHaveText(verdict);

        // A replay or a late answer in the other tab must never add a conversion.
        await second.locator('#replay').click();
        await second.locator('input[value=pool]').check();
        await second.locator('#submit').click();
        await expect(second.locator('#verdict')).toHaveText('Root cause found.');
        await expect
            .poll(() => events.map((e) => e.event))
            .toEqual(correct ? ['$flag_exposure', 'drill_resolved'] : ['$flag_exposure']);
        expect(new Set(events.map((e) => e.identifier)).size).toBe(1);
    });
}

test('resumes a legacy first attempt under its original identity', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.addInitScript(() => {
        localStorage.setItem('first-minute.participant.v1', 'returning-learner');
        localStorage.setItem(
            'first-minute.first-attempt.v1.browser-test',
            JSON.stringify({
                measured: true,
                layout: 'guided',
                deadline: Date.now() + 40000,
            }),
        );
    });
    await page.goto('/');
    await expect(page.locator('#guide')).toBeVisible();
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect
        .poll(() => events.map((e) => [e.event, e.identifier]))
        .toEqual([['drill_resolved', 'returning-learner']]);
    await page.reload();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
});
