// @vitest-environment jsdom
import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import { act, StrictMode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useSocialProofExperiment } from '@/lib/use-social-proof-experiment';
import { Providers } from './providers';

const fetchMock = vi.hoisted(() => vi.fn<typeof fetch>());
const createdInstances = vi.hoisted((): IFlagsmith[] => []);

// The browser build sends requests through its own XMLHttpRequest wrapper; route them to the
// stub through init's documented fetch option while keeping the real SDK under test.
vi.mock('@flagsmith/flagsmith', async (importOriginal) => {
    const sdkModule = await importOriginal<typeof import('@flagsmith/flagsmith')>();
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
});

const ENVIRONMENT_KEY = 'test-client-key';
const VISITOR_ID = '6f1c3c1e-5b7a-4d2e-9f8a-3c2b1a0d9e8f';
const EVENTS_URL = 'https://events.api.flagsmith.com/v1/events';

let container: HTMLDivElement;
let root: Root;

function ExperimentStateProbe() {
    return <output>{JSON.stringify(useSocialProofExperiment())}</output>;
}

const renderedState = () => JSON.parse(container.textContent ?? 'null');

const identityResponse = (variant: string, inExperiment: boolean) =>
    new Response(
        JSON.stringify({
            identifier: VISITOR_ID,
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

const requestsTo = (url: string) => fetchMock.mock.calls.filter(([input]) => String(input).startsWith(url));

const sentEvents = () =>
    requestsTo(EVENTS_URL).flatMap(([, init]) => {
        const body = JSON.parse(String(init?.body)) as { events?: unknown[] } | unknown[];
        return (Array.isArray(body) ? body : (body.events ?? [])) as Array<Record<string, unknown>>;
    });

async function renderWithFlagsmith(environmentKey: string | null) {
    await act(async () => {
        root.render(
            <StrictMode>
                <Providers environmentKey={environmentKey} visitorId={VISITOR_ID}>
                    <ExperimentStateProbe />
                </Providers>
            </StrictMode>,
        );
    });
}

async function flushSdkEvents() {
    await act(async () => {
        await Promise.all(createdInstances.map((instance) => instance.flushEvents()));
    });
}

beforeEach(() => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    fetchMock.mockReset();
    createdInstances.length = 0;
    container = document.createElement('div');
    document.body.append(container);
    root = createRoot(container);
});

afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
});

describe('Providers', () => {
    it('leaves the experiment unavailable and makes no requests without configuration', async () => {
        await renderWithFlagsmith(null);

        expect(renderedState()).toEqual({ status: 'unavailable' });
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it('identifies the visitor once, with the client-side key, even under Strict Mode', async () => {
        fetchMock.mockImplementation(async (input) =>
            String(input).startsWith(EVENTS_URL)
                ? new Response(null, { status: 202 })
                : identityResponse('control', true),
        );

        await renderWithFlagsmith(ENVIRONMENT_KEY);

        const identityRequests = requestsTo('https://edge.api.flagsmith.com/api/v1/identities/');
        expect(identityRequests).toHaveLength(1);
        expect(String(identityRequests[0]?.[0])).toContain(`identifier=${VISITOR_ID}`);
        expect(identityRequests[0]?.[1]?.headers).toMatchObject({ 'X-Environment-Key': ENVIRONMENT_KEY });
    });

    it('reports loading and records no exposure while flags are in flight', async () => {
        fetchMock.mockImplementation(async (input) =>
            String(input).startsWith(EVENTS_URL)
                ? new Response(null, { status: 202 })
                : new Promise<Response>(() => {}),
        );

        await renderWithFlagsmith(ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'loading' });
        expect(sentEvents()).toEqual([]);
    });

    it('falls back to unavailable and records no exposure when flags fail to load', async () => {
        fetchMock.mockImplementation(async (input) => {
            if (String(input).startsWith(EVENTS_URL)) {
                return new Response(null, { status: 202 });
            }
            throw new TypeError('Failed to fetch');
        });

        await renderWithFlagsmith(ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'unavailable' });
        expect(sentEvents()).toEqual([]);
    });

    it('records one exposure for the assigned variant under the visitor identity', async () => {
        fetchMock.mockImplementation(async (input) =>
            String(input).startsWith(EVENTS_URL)
                ? new Response(null, { status: 202 })
                : identityResponse('social_proof', true),
        );

        await renderWithFlagsmith(ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'ready', variant: 'social_proof', enrolled: true });
        expect(sentEvents()).toEqual([
            expect.objectContaining({
                event: '$flag_exposure',
                feature_name: 'study_streak_social_proof',
                identifier: VISITOR_ID,
                value: 'social_proof',
            }),
        ]);
    });

    it('records no exposure for a visitor outside the experiment', async () => {
        fetchMock.mockImplementation(async (input) =>
            String(input).startsWith(EVENTS_URL)
                ? new Response(null, { status: 202 })
                : identityResponse('social_proof', false),
        );

        await renderWithFlagsmith(ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'ready', variant: 'control', enrolled: false });
        expect(sentEvents()).toEqual([]);
    });
});
