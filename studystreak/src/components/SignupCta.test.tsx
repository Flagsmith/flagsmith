// @vitest-environment jsdom
import { act } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { SocialProofExperimentState } from '@/lib/experiment';
import { useSocialProofExperiment } from '@/lib/use-social-proof-experiment';
import { render, type Rendered } from '@/test/render';
import { FLAG_LOAD_TIMEOUT_MS, SignupCta, SignupCtaView } from './SignupCta';

vi.mock('@/lib/use-social-proof-experiment', () => ({ useSocialProofExperiment: vi.fn() }));

const STATES = {
    loading: { status: 'loading' },
    unavailable: { status: 'unavailable' },
    control: { status: 'ready', variant: 'control', enrolled: true },
    socialProof: { status: 'ready', variant: 'social_proof', enrolled: true },
} satisfies Record<string, SocialProofExperimentState>;

let rendered: Rendered;

const query = (selector: string) => rendered.container.querySelector<HTMLElement>(selector);
const button = () => rendered.container.querySelector('button');
const slot = () => query('[data-testid="social-proof-slot"]');

async function renderView(experiment: SocialProofExperimentState) {
    rendered = await render(<SignupCtaView experiment={experiment} />);
    return rendered;
}

afterEach(() => rendered.unmount());

describe('SignupCtaView', () => {
    it('renders a plain Sign Up button and an empty slot for the control', async () => {
        await renderView(STATES.control);

        expect(button()?.textContent).toBe('Sign Up');
        expect(button()?.type).toBe('button');
        expect(slot()?.textContent).toBe('');
    });

    it('renders the same button with the social-proof message for the treatment', async () => {
        await renderView(STATES.socialProof);

        expect(button()?.textContent).toBe('Sign Up');
        expect(slot()?.textContent).toBe('🔥 1,240 students joined this week');
    });

    it('renders an identical button in every state that shows one', async () => {
        const buttons: string[] = [];
        for (const state of [STATES.control, STATES.socialProof, STATES.unavailable]) {
            await renderView(state);
            buttons.push(button()?.outerHTML ?? '');
            await rendered.unmount();
        }
        rendered = await render(null);

        expect(new Set(buttons).size).toBe(1);
    });

    it('reserves the same fixed-height slot in every state', async () => {
        const slotClasses: string[] = [];
        for (const state of Object.values(STATES)) {
            await renderView(state);
            slotClasses.push(slot()?.className ?? 'missing');
            await rendered.unmount();
        }
        rendered = await render(null);

        expect(new Set(slotClasses).size).toBe(1);
        expect(slotClasses[0]).toContain('h-6');
    });

    it('shows neither variant while loading, keeping the button footprint', async () => {
        await renderView(STATES.loading);

        expect(button()).toBeNull();
        expect(slot()?.textContent).toBe('');
        expect(query('[data-testid="signup-cta"]')?.getAttribute('aria-busy')).toBe('true');
        const placeholder = query('[data-testid="signup-cta-placeholder"]');
        expect(placeholder?.getAttribute('aria-hidden')).toBe('true');
        expect(placeholder?.className).toContain('h-12 w-40');
        await rendered.unmount();

        await renderView(STATES.control);
        expect(button()?.className).toContain('h-12 w-40');
    });

    it('falls back to the plain button without a message when unavailable', async () => {
        await renderView(STATES.unavailable);

        expect(button()?.textContent).toBe('Sign Up');
        expect(slot()?.textContent).toBe('');
        expect(query('[data-testid="signup-cta"]')?.getAttribute('aria-busy')).toBe('false');
    });

    it('shows no message to a visitor outside the experiment', async () => {
        await renderView({ status: 'ready', variant: 'control', enrolled: false });

        expect(slot()?.textContent).toBe('');
    });
});

describe('SignupCta', () => {
    const mockedHook = vi.mocked(useSocialProofExperiment);

    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('renders the variant the experiment hook resolves', async () => {
        mockedHook.mockReturnValue(STATES.socialProof);
        rendered = await render(<SignupCta />);

        expect(slot()?.textContent).toBe('🔥 1,240 students joined this week');
    });

    it('falls back to the plain button when flags take too long, and keeps it', async () => {
        mockedHook.mockReturnValue(STATES.loading);
        rendered = await render(<SignupCta />);
        expect(button()).toBeNull();

        await act(async () => vi.advanceTimersByTime(FLAG_LOAD_TIMEOUT_MS));
        expect(button()?.textContent).toBe('Sign Up');

        mockedHook.mockReturnValue(STATES.socialProof);
        await rendered.rerender(<SignupCta />);
        expect(slot()?.textContent).toBe('');
    });

    it('does not time out once the variant has resolved', async () => {
        mockedHook.mockReturnValue(STATES.control);
        rendered = await render(<SignupCta />);

        await act(async () => vi.advanceTimersByTime(FLAG_LOAD_TIMEOUT_MS * 2));
        mockedHook.mockReturnValue(STATES.socialProof);
        await rendered.rerender(<SignupCta />);

        expect(slot()?.textContent).toBe('🔥 1,240 students joined this week');
    });
});
