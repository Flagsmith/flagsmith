// @vitest-environment jsdom
import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import { act } from 'react';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushEventsWhenPageIsHidden, Providers, withKeepaliveForEvents } from '@/app/providers';
import { installDialogPolyfill } from '@/test/dialog';
import {
    EVENTS_URL,
    flushAll,
    identityResponse,
    requestsTo,
    sentEvents,
    serveFlagsmithApi,
    TEST_ENVIRONMENT_KEY,
    TEST_VISITOR_ID,
} from '@/test/fake-flagsmith-api';
import { render, type Rendered } from '@/test/render';
import { SignupCta } from './SignupCta';

const fetchMock = vi.hoisted(() => vi.fn<typeof fetch>());
const createdInstances = vi.hoisted((): IFlagsmith[] => []);

vi.mock('@flagsmith/flagsmith', async (importOriginal) => {
    const { sdkModuleUsingFetch } = await import('@/test/fake-flagsmith-api');
    return sdkModuleUsingFetch(importOriginal, fetchMock, createdInstances);
});

const EXPOSED_AT_MS = 1_700_000_000_000;
let rendered: Rendered;

const signUpButton = () => rendered.container.querySelector<HTMLButtonElement>('[data-testid="signup-cta"] button')!;
const signupClicks = () => sentEvents(fetchMock).filter((event) => event.event === 'signup_clicked');
const flushSdk = () => act(() => flushAll(createdInstances));

async function renderCta(variant: string, inExperiment = true) {
    serveFlagsmithApi(fetchMock, async () => identityResponse(variant, inExperiment));
    rendered = await render(
        <Providers environmentKey={TEST_ENVIRONMENT_KEY} visitorId={TEST_VISITOR_ID}>
            <SignupCta />
        </Providers>,
    );
    await flushSdk();
}

async function clickSignUpAt(nowMs: number) {
    vi.spyOn(Date, 'now').mockReturnValue(nowMs);
    await act(async () => signUpButton().click());
    await flushSdk();
}

beforeAll(installDialogPolyfill);

beforeEach(() => {
    fetchMock.mockReset();
    createdInstances.length = 0;
    window.localStorage.clear();
    vi.spyOn(Date, 'now').mockReturnValue(EXPOSED_AT_MS);
});

afterEach(() => rendered.unmount());

describe('signup_clicked tracking', () => {
    it('sends the first click with the seconds since exposure, under the visitor identity', async () => {
        await renderCta('social_proof');
        await clickSignUpAt(EXPOSED_AT_MS + 4_200);

        expect(signupClicks()).toEqual([
            expect.objectContaining({ event: 'signup_clicked', identifier: TEST_VISITOR_ID, value: '4.2' }),
        ]);
        expect(rendered.container.querySelector('dialog')?.open).toBe(true);
    });

    it('counts a repeated click, or a click after a reload, only once', async () => {
        await renderCta('control');
        await clickSignUpAt(EXPOSED_AT_MS + 1_000);
        await clickSignUpAt(EXPOSED_AT_MS + 2_000);
        await rendered.unmount();

        await renderCta('control');
        await clickSignUpAt(EXPOSED_AT_MS + 60_000);

        expect(signupClicks()).toHaveLength(1);
        expect(signupClicks()[0]).toMatchObject({ value: '1' });
    });

    it('measures from the first exposure even after a reload', async () => {
        await renderCta('social_proof');
        await rendered.unmount();

        vi.spyOn(Date, 'now').mockReturnValue(EXPOSED_AT_MS + 30_000);
        await renderCta('social_proof');
        await clickSignUpAt(EXPOSED_AT_MS + 45_000);

        expect(signupClicks()).toEqual([expect.objectContaining({ value: '45' })]);
    });

    it('does not count page views as clicks', async () => {
        await renderCta('social_proof');

        expect(signupClicks()).toEqual([]);
    });

    it('sends nothing for a visitor outside the experiment, but still opens the form', async () => {
        await renderCta('social_proof', false);
        await clickSignUpAt(EXPOSED_AT_MS + 1_000);

        expect(signupClicks()).toEqual([]);
        expect(rendered.container.querySelector('dialog')?.open).toBe(true);
    });
});

describe('flushEventsWhenPageIsHidden', () => {
    function setVisibility(state: DocumentVisibilityState) {
        Object.defineProperty(document, 'visibilityState', { configurable: true, value: state });
    }

    afterEach(() => setVisibility('visible'));

    it('sends buffered events once when the page is hidden and then unloaded', async () => {
        await renderCta('control');
        fetchMock.mockClear();
        createdInstances[0]!.trackEvent('custom_event');

        setVisibility('hidden');
        document.dispatchEvent(new Event('visibilitychange'));
        window.dispatchEvent(new Event('pagehide'));
        await flushSdk();

        expect(requestsTo(fetchMock, EVENTS_URL)).toHaveLength(1);
        expect(sentEvents(fetchMock).map((event) => event.event)).toEqual(['custom_event']);
    });

    it('does not flush when the page becomes visible', async () => {
        rendered = await render(null);
        const flushEvents = vi.fn(async () => {});
        const stop = flushEventsWhenPageIsHidden({ flushEvents });

        setVisibility('visible');
        document.dispatchEvent(new Event('visibilitychange'));
        expect(flushEvents).not.toHaveBeenCalled();

        stop();
        setVisibility('hidden');
        document.dispatchEvent(new Event('visibilitychange'));
        window.dispatchEvent(new Event('pagehide'));
        expect(flushEvents).not.toHaveBeenCalled();
    });
});

describe('withKeepaliveForEvents', () => {
    const fetchImpl = vi.fn<typeof fetch>(async () => new Response(null, { status: 202 }));
    const keepaliveFetch = withKeepaliveForEvents(fetchImpl);
    const eventsRequest = {
        method: 'POST',
        body: JSON.stringify({ events: [{ event: 'signup_clicked' }] }),
        headers: { 'Content-Type': 'application/json; charset=utf-8', 'X-Environment-Key': TEST_ENVIRONMENT_KEY },
    };

    beforeEach(async () => {
        rendered = await render(null);
        fetchImpl.mockClear();
    });

    it('adds keepalive to events requests and leaves their URL, headers and body untouched', async () => {
        await keepaliveFetch(EVENTS_URL, eventsRequest);

        expect(fetchImpl).toHaveBeenCalledExactlyOnceWith(EVENTS_URL, { ...eventsRequest, keepalive: true });
    });

    it('leaves flag requests unchanged', async () => {
        const identityRequest = { method: 'GET', cache: 'no-cache' as const, headers: { 'X-Environment-Key': 'key' } };
        await keepaliveFetch('https://edge.api.flagsmith.com/api/v1/identities/?identifier=x', identityRequest);

        expect(fetchImpl.mock.calls[0]?.[1]).toBe(identityRequest);
    });

    it('sends batches too large for keepalive without it', async () => {
        const largeRequest = { ...eventsRequest, body: 'x'.repeat(61 * 1024) };
        await keepaliveFetch(EVENTS_URL, largeRequest);

        expect(fetchImpl.mock.calls[0]?.[1]).toBe(largeRequest);
    });
});
