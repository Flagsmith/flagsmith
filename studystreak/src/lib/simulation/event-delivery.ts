import { TRACKED_EVENTS, type TrackedEvent } from './dataset';

const EVENTS_ENDPOINT_PATH = '/v1/events';

export type DeliveryTracker = {
    /** Pass to the SDK's `fetch` option. */
    fetch: typeof fetch;
    /** Events the events API acknowledged with a 2xx response, by name. */
    confirmed(): Record<TrackedEvent, number>;
    /** Batch posts that failed (non-2xx or network error). The SDK may retry a failed batch. */
    failedAttempts(): number;
};

function eventNames(body: unknown): string[] {
    try {
        const parsed = JSON.parse(String(body)) as { events?: Array<{ event?: unknown }> };
        return (parsed.events ?? []).map((event) => String(event.event));
    } catch {
        return [];
    }
}

export function createDeliveryTracker(fetchImpl: typeof fetch = fetch): DeliveryTracker {
    const confirmed = Object.fromEntries(TRACKED_EVENTS.map((event) => [event, 0])) as Record<TrackedEvent, number>;
    let failedAttempts = 0;

    const trackingFetch: typeof fetch = async (input, init) => {
        const url = input instanceof Request ? input.url : String(input);
        if (!url.endsWith(EVENTS_ENDPOINT_PATH)) {
            return fetchImpl(input, init);
        }
        let response: Response;
        try {
            response = await fetchImpl(input, init);
        } catch (error) {
            failedAttempts++;
            throw error;
        }
        if (!response.ok) {
            failedAttempts++;
            return response;
        }
        for (const name of eventNames(init?.body)) {
            if (name in confirmed) {
                confirmed[name as TrackedEvent]++;
            }
        }
        return response;
    };

    return { fetch: trackingFetch, confirmed: () => ({ ...confirmed }), failedAttempts: () => failedAttempts };
}
