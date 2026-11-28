import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import type { Mock } from 'vitest';

export const TEST_ENVIRONMENT_KEY = 'test-client-key';
export const TEST_VISITOR_ID = '6f1c3c1e-5b7a-4d2e-9f8a-3c2b1a0d9e8f';
export const IDENTITIES_URL = 'https://edge.api.flagsmith.com/api/v1/identities/';
export const EVENTS_URL = 'https://events.api.flagsmith.com/v1/events';

type FetchMock = Mock<typeof fetch>;
type IdentityReply = () => Promise<Response>;

export const identityResponse = (variant: string, inExperiment: boolean) =>
    new Response(
        JSON.stringify({
            identifier: TEST_VISITOR_ID,
            traits: [],
            flags: [
                {
                    enabled: true,
                    feature_state_value: variant,
                    variant,
                    feature: { id: 1, name: 'study_streak_social_proof' },
                    metadata: { experiment: { id: 7, name: 'study_streak_social_proof', in_experiment: inExperiment } },
                },
            ],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
    );

export function serveFlagsmithApi(fetchMock: FetchMock, replyToIdentity: IdentityReply) {
    fetchMock.mockImplementation(async (input) =>
        String(input).startsWith(EVENTS_URL) ? new Response(null, { status: 202 }) : replyToIdentity(),
    );
}

export const requestsTo = (fetchMock: FetchMock, url: string) =>
    fetchMock.mock.calls.filter(([input]) => String(input).startsWith(url));

export const sentEvents = (fetchMock: FetchMock) =>
    requestsTo(fetchMock, EVENTS_URL).flatMap(([, init]) => {
        const body = JSON.parse(String(init?.body)) as { events?: unknown[] } | unknown[];
        return (Array.isArray(body) ? body : (body.events ?? [])) as Array<Record<string, unknown>>;
    });

// The browser build sends requests through its own XMLHttpRequest wrapper. For vi.mock: routes the
// real SDK's requests to the stub through init's documented fetch option and records each instance.
export async function sdkModuleUsingFetch(
    importOriginal: () => Promise<typeof import('@flagsmith/flagsmith')>,
    fetchMock: FetchMock,
    createdInstances: IFlagsmith[],
) {
    const sdkModule = await importOriginal();
    return {
        ...sdkModule,
        createFlagsmithInstance: () => {
            const instance = sdkModule.createFlagsmithInstance();
            const init = instance.init.bind(instance);
            instance.init = (options) => init({ ...options, fetch: fetchMock });
            createdInstances.push(instance);
            return instance;
        },
    };
}

export const flushAll = (createdInstances: IFlagsmith[]) =>
    Promise.all(createdInstances.map((instance) => instance.flushEvents()));
