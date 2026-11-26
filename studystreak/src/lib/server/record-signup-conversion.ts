import { Flagsmith } from '@flagsmith/nodejs';
import { SIGNED_UP_EVENT } from '@/lib/experiment';

const EVENTS_ENDPOINT_PATH = '/v1/events';
// Covers the SDK's three attempts per batch (3 s timeout each, with backoff) in the worst case.
const DELIVERY_TIMEOUT_MS = 12_000;

// A client per request: flushEvents() never reports failure, so a dedicated client lets us observe
// whether the events API accepted this signup's batch before telling the visitor they signed up.
export async function recordSignupConversion(
    visitorId: string,
    serverKey: string,
    fetchImpl: typeof fetch = fetch,
): Promise<boolean> {
    let delivered = false;
    const observingFetch: typeof fetch = async (input, init) => {
        const response = await fetchImpl(input, init);
        if (response.ok && String(input instanceof Request ? input.url : input).endsWith(EVENTS_ENDPOINT_PATH)) {
            delivered = true;
        }
        return response;
    };

    const flagsmith = new Flagsmith({ environmentKey: serverKey, enableEvents: true, fetch: observingFetch });
    flagsmith.trackEvent(SIGNED_UP_EVENT, { identifier: visitorId });
    await flagsmith.close(DELIVERY_TIMEOUT_MS);
    return delivered;
}
