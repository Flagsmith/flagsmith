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
        // Read the body before dispatch: for fetch(request) it lives on the Request, which fetch then consumes.
        const body = init?.body ?? (input instanceof Request ? await input.clone().text() : undefined);
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
        for (const name of eventNames(body)) {
            if (name in confirmed) {
                confirmed[name as TrackedEvent]++;
            }
        }
        return response;
    };

    return { fetch: trackingFetch, confirmed: () => ({ ...confirmed }), failedAttempts: () => failedAttempts };
}
