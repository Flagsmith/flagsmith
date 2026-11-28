// @vitest-environment jsdom
import { createFlagsmithInstance } from '@flagsmith/flagsmith';
import { describe, expect, it, vi } from 'vitest';
import { EVENTS_URL, identityResponse, TEST_ENVIRONMENT_KEY, TEST_VISITOR_ID } from '@/test/fake-flagsmith-api';
import { withKeepaliveForEvents } from './providers';

type RecordedRequest = { url: string; init: RequestInit | undefined };

async function recordSdkRequests(wrap: (fetchImpl: typeof fetch) => typeof fetch) {
    const requests: RecordedRequest[] = [];
    const network = vi.fn<typeof fetch>(async (input, init) => {
        requests.push({ url: String(input), init });
        return String(input).startsWith(EVENTS_URL)
            ? new Response(null, { status: 202 })
            : identityResponse('control', true);
    });
    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000);

    const flagsmith = createFlagsmithInstance();
    await flagsmith.init({
        environmentID: TEST_ENVIRONMENT_KEY,
        identity: TEST_VISITOR_ID,
        enableEvents: true,
        fetch: wrap(network),
    });
    flagsmith.getExperimentFlag('study_streak_social_proof');
    flagsmith.trackEvent('signup_clicked', { value: 4.2 });
    await flagsmith.flushEvents();
    await flagsmith.close(1000);
    return requests;
}

describe('withKeepaliveForEvents with the real SDK', () => {
    it('changes nothing about the requests except keepalive on the events batch', async () => {
        const plain = await recordSdkRequests((fetchImpl) => fetchImpl);
        const wrapped = await recordSdkRequests(withKeepaliveForEvents);

        expect(wrapped.map((request) => request.url)).toEqual(plain.map((request) => request.url));
        expect(plain.map((request) => request.url)).toEqual([expect.stringContaining('/identities/'), EVENTS_URL]);

        const [plainIdentity, plainEvents] = plain;
        const [wrappedIdentity, wrappedEvents] = wrapped;
        expect(wrappedIdentity?.init).toEqual(plainIdentity?.init);
        expect(wrappedIdentity?.init).not.toHaveProperty('keepalive');

        const { keepalive, ...eventsInit } = wrappedEvents?.init ?? {};
        expect(keepalive).toBe(true);
        expect({ ...eventsInit, signal: undefined }).toEqual({ ...plainEvents?.init, signal: undefined });
        expect(new Headers(eventsInit.headers).get('X-Environment-Key')).toBe(TEST_ENVIRONMENT_KEY);
        expect(JSON.parse(String(eventsInit.body)).events.map((event: { event: string }) => event.event)).toEqual([
            '$flag_exposure',
            'signup_clicked',
        ]);
    });
});
