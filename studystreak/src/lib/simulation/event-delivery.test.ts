import { describe, expect, it, vi } from 'vitest';
import { createDeliveryTracker } from './event-delivery';

const EVENTS_URL = 'https://events.api.flagsmith.com/v1/events';
const batch = (...events: string[]) => ({
    method: 'POST',
    body: JSON.stringify({ events: events.map((event) => ({ event, identifier: 'sim-1' })) }),
});

describe('createDeliveryTracker', () => {
    it('counts events only once the events API acknowledges them', async () => {
        const tracker = createDeliveryTracker(vi.fn(async () => new Response(null, { status: 202 })));

        await tracker.fetch(EVENTS_URL, batch('$flag_exposure', 'signup_clicked', 'signed_up', 'signup_clicked'));

        expect(tracker.confirmed()).toEqual({ $flag_exposure: 1, signup_clicked: 2, signed_up: 1 });
        expect(tracker.failedAttempts()).toBe(0);
    });

    it('counts events when the SDK passes a Request instead of a body in init', async () => {
        // Given
        const fetchImpl = vi.fn(async (input: RequestInfo | URL) => {
            await (input as Request).text(); // the real fetch consumes the request body
            return new Response(null, { status: 202 });
        });
        const tracker = createDeliveryTracker(fetchImpl as typeof fetch);
        const request = new Request(EVENTS_URL, batch('$flag_exposure', 'signed_up'));

        // When
        await tracker.fetch(request);

        // Then
        expect(tracker.confirmed()).toEqual({ $flag_exposure: 1, signup_clicked: 0, signed_up: 1 });
        expect(fetchImpl).toHaveBeenCalledOnce();
    });

    it('does not count rejected batches', async () => {
        const tracker = createDeliveryTracker(vi.fn(async () => new Response(null, { status: 503 })));

        const response = await tracker.fetch(EVENTS_URL, batch('signed_up'));

        expect(response.status).toBe(503);
        expect(tracker.confirmed().signed_up).toBe(0);
        expect(tracker.failedAttempts()).toBe(1);
    });

    it('does not count batches lost to network errors, and still surfaces the error', async () => {
        const tracker = createDeliveryTracker(vi.fn(async () => Promise.reject(new TypeError('fetch failed'))));

        await expect(tracker.fetch(EVENTS_URL, batch('signed_up'))).rejects.toThrow('fetch failed');
        expect(tracker.confirmed().signed_up).toBe(0);
        expect(tracker.failedAttempts()).toBe(1);
    });

    it('passes other requests through untouched and uncounted', async () => {
        const network = vi.fn(async () => new Response('{}', { status: 200 }));
        const tracker = createDeliveryTracker(network);
        const init = { method: 'POST', body: '{"identifier":"sim-1"}' };

        await tracker.fetch('https://edge.api.flagsmith.com/api/v1/identities/', init);

        expect(network).toHaveBeenCalledWith('https://edge.api.flagsmith.com/api/v1/identities/', init);
        expect(tracker.confirmed()).toEqual({ $flag_exposure: 0, signup_clicked: 0, signed_up: 0 });
    });
});
