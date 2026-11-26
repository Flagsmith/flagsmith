// @vitest-environment jsdom
import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import { act, StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useSocialProofExperiment } from '@/lib/use-social-proof-experiment';
import {
    flushAll,
    IDENTITIES_URL,
    identityResponse,
    requestsTo,
    sentEvents,
    serveFlagsmithApi,
    TEST_ENVIRONMENT_KEY,
    TEST_VISITOR_ID,
} from '@/test/fake-flagsmith-api';
import { render, type Rendered } from '@/test/render';
import { Providers } from './providers';

const fetchMock = vi.hoisted(() => vi.fn<typeof fetch>());
const createdInstances = vi.hoisted((): IFlagsmith[] => []);

vi.mock('@flagsmith/flagsmith', async (importOriginal) => {
    const { sdkModuleUsingFetch } = await import('@/test/fake-flagsmith-api');
    return sdkModuleUsingFetch(importOriginal, fetchMock, createdInstances);
});

function ExperimentStateProbe() {
    return <output>{JSON.stringify(useSocialProofExperiment())}</output>;
}

let rendered: Rendered;

const renderedState = () => JSON.parse(rendered.container.textContent ?? 'null');

async function renderWithFlagsmith(environmentKey: string | null) {
    rendered = await render(
        <StrictMode>
            <Providers environmentKey={environmentKey} visitorId={TEST_VISITOR_ID}>
                <ExperimentStateProbe />
            </Providers>
        </StrictMode>,
    );
}

const flushSdkEvents = () => act(() => flushAll(createdInstances));

beforeEach(() => {
    fetchMock.mockReset();
    createdInstances.length = 0;
});

afterEach(() => rendered.unmount());

describe('Providers', () => {
    it('leaves the experiment unavailable and makes no requests without configuration', async () => {
        await renderWithFlagsmith(null);

        expect(renderedState()).toEqual({ status: 'unavailable' });
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it('identifies the visitor once, with the client-side key, even under Strict Mode', async () => {
        serveFlagsmithApi(fetchMock, async () => identityResponse('control', true));

        await renderWithFlagsmith(TEST_ENVIRONMENT_KEY);

        const identityRequests = requestsTo(fetchMock, IDENTITIES_URL);
        expect(identityRequests).toHaveLength(1);
        expect(String(identityRequests[0]?.[0])).toContain(`identifier=${TEST_VISITOR_ID}`);
        expect(identityRequests[0]?.[1]?.headers).toMatchObject({ 'X-Environment-Key': TEST_ENVIRONMENT_KEY });
    });

    it('reports loading and records no exposure while flags are in flight', async () => {
        serveFlagsmithApi(fetchMock, () => new Promise<Response>(() => {}));

        await renderWithFlagsmith(TEST_ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'loading' });
        expect(sentEvents(fetchMock)).toEqual([]);
    });

    it('falls back to unavailable and records no exposure when flags fail to load', async () => {
        serveFlagsmithApi(fetchMock, async () => {
            throw new TypeError('Failed to fetch');
        });

        await renderWithFlagsmith(TEST_ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'unavailable' });
        expect(sentEvents(fetchMock)).toEqual([]);
    });

    it('records one exposure for the assigned variant under the visitor identity', async () => {
        serveFlagsmithApi(fetchMock, async () => identityResponse('social_proof', true));

        await renderWithFlagsmith(TEST_ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'ready', variant: 'social_proof', enrolled: true });
        expect(sentEvents(fetchMock)).toEqual([
            expect.objectContaining({
                event: '$flag_exposure',
                feature_name: 'study_streak_social_proof',
                identifier: TEST_VISITOR_ID,
                value: 'social_proof',
            }),
        ]);
    });

    it('records no exposure for a visitor outside the experiment', async () => {
        serveFlagsmithApi(fetchMock, async () => identityResponse('social_proof', false));

        await renderWithFlagsmith(TEST_ENVIRONMENT_KEY);
        await flushSdkEvents();

        expect(renderedState()).toEqual({ status: 'ready', variant: 'control', enrolled: false });
        expect(sentEvents(fetchMock)).toEqual([]);
    });
});
