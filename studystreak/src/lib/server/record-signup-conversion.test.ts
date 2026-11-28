import { describe, expect, it, vi } from 'vitest';
import { recordSignupConversion } from './record-signup-conversion';

const VISITOR_ID = '6f1c3c1e-5b7a-4d2e-9f8a-3c2b1a0d9e8f';

const eventsApi = (status: number) => vi.fn<typeof fetch>(async () => new Response(null, { status }));

const postedEvents = (fetchMock: ReturnType<typeof eventsApi>) =>
    fetchMock.mock.calls.flatMap(([, init]) => {
        const body = JSON.parse(String(init?.body)) as { events?: unknown[] } | unknown[];
        return Array.isArray(body) ? body : (body.events ?? []);
    });

describe('recordSignupConversion', () => {
    it('sends one signed_up event for the visitor, with the server key, and confirms delivery', async () => {
        const fetchMock = eventsApi(202);

        await expect(recordSignupConversion(VISITOR_ID, 'ser.test', fetchMock)).resolves.toBe(true);

        expect(fetchMock).toHaveBeenCalledTimes(1);
        const [url, init] = fetchMock.mock.calls[0]!;
        expect(String(url)).toBe('https://events.api.flagsmith.com/v1/events');
        expect(new Headers(init?.headers).get('X-Environment-Key')).toBe('ser.test');
        expect(postedEvents(fetchMock)).toEqual([
            expect.objectContaining({ event: 'signed_up', identifier: VISITOR_ID, value: null }),
        ]);
    });

    it.each([400, 401])('reports failure when the events API answers %i', async (status) => {
        await expect(recordSignupConversion(VISITOR_ID, 'ser.test', eventsApi(status))).resolves.toBe(false);
    });
});
