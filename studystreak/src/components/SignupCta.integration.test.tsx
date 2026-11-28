// @vitest-environment jsdom
import type { IFlagsmith } from '@flagsmith/flagsmith/types';
import { act } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Providers } from '@/app/providers';
import {
    flushAll,
    identityResponse,
    sentEvents,
    serveFlagsmithApi,
    TEST_ENVIRONMENT_KEY,
    TEST_VISITOR_ID,
} from '@/test/fake-flagsmith-api';
import { render, type Rendered } from '@/test/render';
import { FLAG_LOAD_TIMEOUT_MS, SignupCta } from './SignupCta';

const fetchMock = vi.hoisted(() => vi.fn<typeof fetch>());
const createdInstances = vi.hoisted((): IFlagsmith[] => []);

vi.mock('@flagsmith/flagsmith', async (importOriginal) => {
    const { sdkModuleUsingFetch } = await import('@/test/fake-flagsmith-api');
    return sdkModuleUsingFetch(importOriginal, fetchMock, createdInstances);
});

let rendered: Rendered;

const button = () => rendered.container.querySelector<HTMLButtonElement>('[data-testid="signup-cta"] button');
const socialProofText = () => rendered.container.querySelector('[data-testid="social-proof-slot"]')?.textContent;
const exposures = () => sentEvents(fetchMock).filter((event) => event.event === '$flag_exposure');

async function renderCta() {
    rendered = await render(
        <Providers environmentKey={TEST_ENVIRONMENT_KEY} visitorId={TEST_VISITOR_ID}>
            <SignupCta />
        </Providers>,
    );
    await act(() => flushAll(createdInstances));
}

beforeEach(() => {
    fetchMock.mockReset();
    createdInstances.length = 0;
});

afterEach(() => rendered.unmount());

describe('SignupCta with the Flagsmith SDK', () => {
    it.each([
        ['control', ''],
        ['social_proof', '🔥 1,240 students joined this week'],
    ])('shows the %s variant and records an exposure for exactly that variant', async (variant, message) => {
        serveFlagsmithApi(fetchMock, async () => identityResponse(variant, true));

        await renderCta();

        expect(button()?.textContent).toBe('Sign Up');
        expect(socialProofText()).toBe(message);
        expect(exposures()).toEqual([expect.objectContaining({ identifier: TEST_VISITOR_ID, value: variant })]);
    });

    it('shows no variant and records no exposure while loading', async () => {
        serveFlagsmithApi(fetchMock, () => new Promise<Response>(() => {}));

        await renderCta();

        expect(button()).toBeNull();
        expect(exposures()).toEqual([]);
    });

    it('shows the plain button and records no exposure when flags fail to load', async () => {
        serveFlagsmithApi(fetchMock, async () => {
            throw new TypeError('Failed to fetch');
        });

        await renderCta();

        expect(button()?.textContent).toBe('Sign Up');
        expect(socialProofText()).toBe('');
        expect(exposures()).toEqual([]);
    });

    describe('when flags arrive after the timeout', () => {
        beforeEach(() => {
            vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
        });

        afterEach(() => {
            vi.useRealTimers();
        });

        it('keeps the plain button and records no exposure', async () => {
            let deliverFlags: (response: Response) => void = () => {};
            serveFlagsmithApi(fetchMock, () => new Promise<Response>((resolve) => (deliverFlags = resolve)));

            await renderCta();
            await act(async () => vi.advanceTimersByTime(FLAG_LOAD_TIMEOUT_MS));
            await act(async () => deliverFlags(identityResponse('social_proof', true)));
            await act(() => flushAll(createdInstances));

            expect(button()?.textContent).toBe('Sign Up');
            expect(socialProofText()).toBe('');
            expect(exposures()).toEqual([]);
        });
    });
});
