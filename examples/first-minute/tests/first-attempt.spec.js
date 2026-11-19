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
        await expect(second.locator('#preflight')).toBeHidden();

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
        .toEqual([
            ['$flag_exposure', 'returning-learner'],
            ['drill_resolved', 'returning-learner'],
        ]);
    await page.reload();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
});

test('a stalled Flagsmith lookup still allows an unmeasured practice round', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.route('**/api/v1/identities/**', () => {});
    await page.goto('/index.html');
    await expect(page.locator('#mode')).toHaveText('Practice mode · experiment offline', { timeout: 8000 });
    await page.locator('#start').focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('#desk')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Release log' })).toBeFocused();
    await page.getByRole('button', { name: 'Traces' }).click();
    await page.getByRole('link', { name: 'First Minute' }).click();
    await expect(page).toHaveURL(/\/index\.html#briefing$/);
    await expect(page.getByRole('button', { name: 'Traces' })).toHaveAttribute('aria-pressed', 'true');
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    expect(events).toEqual([]);
});

test('the standalone drill remains playable when both storage mechanisms are blocked', async ({ page }) => {
    await page.addInitScript(() => {
        for (const name of ['indexedDB', 'localStorage']) {
            Object.defineProperty(window, name, {
                get() {
                    throw new DOMException('Storage blocked', 'SecurityError');
                },
            });
        }
    });
    await page.route('**/offline-practice.html', (route) =>
        route.fulfill({ contentType: 'text/html', path: 'dist/first-minute.html' }),
    );
    await page.goto('/offline-practice.html');
    await page.locator('#start').click();
    await expect(page.locator('#mode')).toHaveText('Practice · excluded from experiment');
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
});

test('a returning participant can answer with the flag endpoint unavailable', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect.poll(() => events.map((event) => event.event)).toEqual(['$flag_exposure']);

    let repeatedLookups = 0;
    await page.route('**/api/v1/identities/**', (route) => {
        repeatedLookups++;
        return route.abort();
    });
    await page.reload();
    await expect(page.locator('#guide')).toBeVisible({ timeout: 2500 });
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    await expect.poll(() => events.map((event) => event.event)).toEqual(['$flag_exposure', 'drill_resolved']);
    expect(events[0].identifier).toBe(events[1].identifier);
    expect(repeatedLookups).toBe(0);
});

test('a correct answer after the deadline stays expired across a reload', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.clock.install();
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await page.locator('input[value=pool]').check();
    await expect.poll(() => events.map((event) => event.event)).toEqual(['$flag_exposure']);
    // Advance wall time without firing the next timer tick, as when resuming a background tab.
    await page.clock.setSystemTime(new Date((await page.evaluate(() => Date.now())) + 61000));
    await page.locator('#form').evaluate((form) => form.requestSubmit());
    await expect(page.locator('#verdict')).toHaveText('Time expired.');
    await page.reload();
    await expect(page.locator('#verdict')).toHaveText('Time expired.');
    expect(events.map((event) => event.event)).toEqual(['$flag_exposure']);
});

for (const practiceFirst of [true, false]) {
    test(`the first ${
        practiceFirst ? 'practice' : 'enrolled'
    } desk determines eligibility across tabs and reloads`, async ({ page, context }) => {
        const events = await interceptSdk(context);
        const offline = await context.newPage();
        const lookup = '**/api/v1/identities/**';
        await offline.route(lookup, (route) => route.abort());
        await Promise.all([page.goto('/'), offline.goto('/')]);
        await expect(offline.locator('#mode')).toHaveText('Practice mode · experiment offline');
        await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
        const [first, second] = practiceFirst ? [offline, page] : [page, offline];
        await first.locator('#start').click();
        await expect(first.locator('#desk')).toBeVisible();
        await second.locator('#start').click();
        for (const tab of [first, second]) {
            await expect(tab.locator('#mode')).toHaveText(
                practiceFirst ? 'Practice · excluded from experiment' : 'Experiment · first attempt',
            );
            await expect(tab.locator('#guide')).toBeVisible({ visible: !practiceFirst });
        }
        await offline.locator('input[value=pool]').check();
        await offline.locator('#submit').click();
        for (const tab of [first, second]) await expect(tab.locator('#verdict')).toHaveText('Root cause found.');

        await offline.unroute(lookup);
        await offline.reload();
        await expect(offline.locator('#verdict')).toHaveText('Root cause found.');
        await offline.locator('#replay').click();
        await offline.locator('input[value=pool]').check();
        await offline.locator('#submit').click();
        await expect(offline.locator('#verdict')).toHaveText('Root cause found.');
        await expect
            .poll(() => events.map((event) => event.event))
            .toEqual(practiceFirst ? [] : ['$flag_exposure', 'drill_resolved']);
        if (!practiceFirst) expect(events[0].identifier).toBe(events[1].identifier);
    });
}

test('a rejected conversion retries with its original time and identity after a reload', async ({ page, context }) => {
    await interceptSdk(context);
    const attempts = [];
    let rejectConversion = true;
    await context.route('**/api/v1/events', (route) => {
        const [event] = route.request().postDataJSON().events;
        attempts.push(event);
        const rejected = rejectConversion && event.event === 'drill_resolved';
        return route.fulfill({
            status: 202,
            json: {
                accepted: rejected ? 0 : 1,
                rejected: rejected ? [{ index: 0, error: 'Test rejection' }] : [],
            },
        });
    });
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#delivery-status')).toContainText('Event delivery unconfirmed');
    rejectConversion = false;
    await page.reload();
    await expect
        .poll(() => attempts.map((e) => e.event))
        .toEqual(['$flag_exposure', 'drill_resolved', 'drill_resolved']);
    expect(attempts[2]).toEqual(attempts[1]);
    expect(attempts[0].timestamp).toBeLessThanOrEqual(attempts[1].timestamp);
    await expect(page.locator('#delivery-status')).toBeHidden();
});

test('a failed save preserves the first answer and withholds the solution', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect.poll(() => events.length).toBe(1);
    await page.evaluate(() => {
        const put = IDBObjectStore.prototype.put;
        IDBObjectStore.prototype.put = function (value, ...args) {
            if (value?.done) throw new DOMException('Test write failure', 'QuotaExceededError');
            return put.call(this, value, ...args);
        };
    });
    await page.locator('input[value=traffic]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#save-error')).toBeVisible();
    await expect(page.locator('#result')).toBeHidden();
    await page.reload();
    await expect(page.locator('#verdict')).toHaveText('Look at the connection queue.');
    await page.locator('#replay').click();
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    expect(events.map((e) => e.event)).toEqual(['$flag_exposure']);
});

test('waiting for storage before the first desk opens does not consume drill time', async ({ page, context }) => {
    await interceptSdk(context);
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.evaluate(() => {
        const now = Date.now;
        let offset = 0;
        Date.now = () => now() + offset;
        const get = IDBObjectStore.prototype.get;
        IDBObjectStore.prototype.get = function (key) {
            if (key === 'first-minute.first-attempt.v1.browser-test') offset = 5000;
            return get.call(this, key);
        };
    });
    await page.locator('#start').click();
    await expect(page.locator('#clock')).toHaveText('60s');
});

test('a reload during exposure delivery recovers the original assignment', async ({ page, context }) => {
    await interceptSdk(context);
    const attempts = [];
    await context.route('**/api/v1/events', (route) => {
        attempts.push(route.request().postDataJSON().events[0]);
        if (attempts.length === 1) return;
        return route.fulfill({ status: 202, json: { accepted: 1, rejected: [] } });
    });
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect.poll(() => attempts.length).toBe(1);
    await page.reload();
    await expect(page.locator('#guide')).toBeVisible();
    await expect.poll(() => attempts.length, { timeout: 15000 }).toBe(2);
    expect(attempts[1]).toEqual(attempts[0]);
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect
        .poll(() => attempts.map((e) => e.event))
        .toEqual(['$flag_exposure', '$flag_exposure', 'drill_resolved']);
});

test('reading an offline briefing leaves the first connected round eligible', async ({ page, context }) => {
    const events = await interceptSdk(context);
    const lookup = '**/api/v1/identities/**';
    await page.route(lookup, (route) => route.abort());
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Practice mode · experiment offline');
    await page.unroute(lookup);
    await page.reload();
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect.poll(() => events.map((e) => e.event)).toEqual(['$flag_exposure']);
});

for (const fallback of [false, true]) {
    test(`two tabs recover the first answer from ${fallback ? 'locked localStorage' : 'IndexedDB'} after a failed save`, async ({
        page,
        context,
    }) => {
        const events = await interceptSdk(context);
        const second = await context.newPage();
        await Promise.all([page.goto('/'), second.goto('/')]);
        for (const tab of [page, second]) await expect(tab.locator('#mode')).toHaveText('Connected to Flagsmith');
        for (const tab of [page, second]) {
            await tab.locator('#start').click();
            await expect(tab.locator('#desk')).toBeVisible();
            await tab.evaluate((blockJournal) => {
                const put = IDBObjectStore.prototype.put;
                IDBObjectStore.prototype.put = function (value, key) {
                    if (value?.done || (blockJournal && String(key).includes('.answer.'))) {
                        throw new DOMException('Test write interruption', 'QuotaExceededError');
                    }
                    return put.call(this, value, key);
                };
            }, fallback);
        }
        await page.locator('input[value=traffic]').check();
        await second.locator('input[value=pool]').check();
        await page.locator('#submit').click();
        await expect(page.locator('#save-error')).toBeVisible();
        await second.locator('#submit').click();
        await expect(second.locator('#save-error')).toBeVisible();
        await Promise.all([page.reload(), second.reload()]);
        for (const tab of [page, second])
            await expect(tab.locator('#verdict')).toHaveText('Look at the connection queue.');
        expect(events.map((e) => e.event)).toEqual(['$flag_exposure']);
    });
}

test('an expired receipt stops retries and keeps the original local verdict', async ({ page, context }) => {
    const attempts = [];
    await page.addInitScript(() => {
        const key = 'first-minute.first-attempt.v1.browser-test';
        if (localStorage.getItem(key)) return;
        const started = Date.now() - 11 * 24 * 60 * 60 * 1000;
        localStorage.setItem(
            key,
            JSON.stringify({
                measured: true,
                done: true,
                identifier: 'late-player',
                layout: 'guided',
                variant: 'guided',
                deadline: started + 60000,
                finishedAt: started + 2000,
                answer: 'pool',
                delivery: { $flag_exposure: true },
            }),
        );
    });
    await context.route('**/api/v1/events', (route) => {
        attempts.push(route.request().postDataJSON().events[0]);
        return route.fulfill({
            status: 400,
            json: { accepted: 0, rejected: [{ index: 0, error: 'timestamp: Timestamp is older than 10 days.' }] },
        });
    });
    await page.goto('/');
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    await expect(page.locator('#delivery-status')).toContainText('delivery window has closed');
    await page.reload();
    await expect(page.locator('#delivery-status')).toContainText('delivery window has closed');
    await page.clock.install();
    await page.evaluate(() => window.dispatchEvent(new Event('online')));
    await page.clock.fastForward(61000);
    expect(attempts.map((event) => event.event)).toEqual(['drill_resolved']);
});

test('a failed first-desk write keeps the solution hidden until storage recovers', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.evaluate(() => {
        const put = IDBObjectStore.prototype.put;
        IDBObjectStore.prototype.put = function (value, key) {
            if (key === 'first-minute.first-attempt.v1.browser-test')
                throw new DOMException('No space', 'QuotaExceededError');
            return put.call(this, value, key);
        };
    });
    await page.locator('#start').click();
    await expect(page.locator('#start')).toHaveText('Reload briefing');
    await expect(page.locator('#desk')).toBeHidden();
    await expect(page.locator('#result')).toBeHidden();
    expect(events).toEqual([]);
    await page.locator('#start').click();
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect(page.locator('#guide')).toBeVisible();
    await expect.poll(() => events.map((e) => e.event)).toEqual(['$flag_exposure']);
});

test('an unavailable attempt database preserves an enrolled round', async ({ page, context }) => {
    const events = await interceptSdk(context);
    await page.addInitScript(() => {
        if (sessionStorage.getItem('block-attempt-db')) {
            IDBFactory.prototype.open = () => {
                throw new DOMException('Database unavailable', 'InvalidStateError');
            };
        }
    });
    await page.goto('/');
    await expect(page.locator('#mode')).toHaveText('Connected to Flagsmith');
    await page.locator('#start').click();
    await expect.poll(() => events.length).toBe(1);
    await page.evaluate(() => sessionStorage.setItem('block-attempt-db', '1'));
    await page.reload();
    await expect(page.locator('#start')).toHaveText('Reload briefing');
    await expect(page.locator('#desk')).toBeHidden();
    await page.evaluate(() => sessionStorage.removeItem('block-attempt-db'));
    await page.locator('#start').click();
    await expect(page.locator('#guide')).toBeVisible();
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect.poll(() => events.map((e) => e.event)).toEqual(['$flag_exposure', 'drill_resolved']);
    expect(events[1].identifier).toBe(events[0].identifier);
});

test('standalone practice still excludes later enrolment when localStorage is unavailable', async ({
    page,
    context,
}) => {
    const events = await interceptSdk(context);
    await page.addInitScript(() => {
        Object.defineProperty(window, 'localStorage', {
            get() {
                throw new DOMException('Storage blocked', 'SecurityError');
            },
        });
    });
    await page.route('**/offline-practice.html', (route) =>
        route.fulfill({ contentType: 'text/html', path: 'dist/first-minute.html' }),
    );
    await page.goto('/offline-practice.html');
    await page.locator('#start').click();
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    await page.goto('/');
    await expect(page.locator('#start')).toBeEnabled();
    await page.locator('#start').click();
    await expect(page.locator('#mode')).toHaveText('Practice · excluded from experiment');
    await page.locator('input[value=pool]').check();
    await page.locator('#submit').click();
    await expect(page.locator('#verdict')).toHaveText('Root cause found.');
    expect(events).toEqual([]);
});
