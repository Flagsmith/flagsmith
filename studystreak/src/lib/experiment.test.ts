import type { IFlagsmithFeature, LoadingState } from '@flagsmith/flagsmith/types';
import { describe, expect, it } from 'vitest';
import { resolveSocialProofExperiment } from './experiment';

const loading = (overrides: Partial<LoadingState>) =>
    ({ isLoading: false, isFetching: false, error: null, source: 'SERVER', ...overrides }) as LoadingState;

const experimentFlag = (variant: string, inExperiment = true): IFlagsmithFeature => ({
    enabled: true,
    value: variant,
    variant,
    experiment: { id: 1, name: 'study_streak_social_proof', inExperiment },
});

describe('resolveSocialProofExperiment', () => {
    it('is unavailable without a Flagsmith provider', () => {
        expect(resolveSocialProofExperiment(undefined, null)).toEqual({ status: 'unavailable' });
    });

    it('is loading until flags arrive from the server', () => {
        expect(
            resolveSocialProofExperiment(loading({ isLoading: true, isFetching: true, source: 'NONE' as never }), null),
        ).toEqual({
            status: 'loading',
        });
    });

    it('is unavailable when the SDK reports an error', () => {
        const state = loading({ error: new Error('network'), source: 'NONE' as never });
        expect(resolveSocialProofExperiment(state, null)).toEqual({ status: 'unavailable' });
    });

    it('ignores flags that did not come from the server', () => {
        const state = loading({ source: 'DEFAULT_FLAGS' as never });
        expect(resolveSocialProofExperiment(state, experimentFlag('social_proof'))).toEqual({ status: 'unavailable' });
    });

    it('is unavailable when the flag is missing from the environment', () => {
        expect(resolveSocialProofExperiment(loading({}), null)).toEqual({ status: 'unavailable' });
    });

    it('resolves the treatment for an enrolled identity', () => {
        expect(resolveSocialProofExperiment(loading({}), experimentFlag('social_proof'))).toEqual({
            status: 'ready',
            variant: 'social_proof',
            enrolled: true,
        });
    });

    it('resolves the control for an enrolled identity', () => {
        expect(resolveSocialProofExperiment(loading({}), experimentFlag('control'))).toEqual({
            status: 'ready',
            variant: 'control',
            enrolled: true,
        });
    });

    it('shows the control to identities outside the experiment', () => {
        expect(resolveSocialProofExperiment(loading({}), experimentFlag('social_proof', false))).toEqual({
            status: 'ready',
            variant: 'control',
            enrolled: false,
        });
    });
});
