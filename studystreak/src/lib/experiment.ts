import type { IFlagsmithFeature, LoadingState } from '@flagsmith/flagsmith/types';

export const SOCIAL_PROOF_FLAG = 'study_streak_social_proof';
export const SOCIAL_PROOF_VARIANT = 'social_proof';
// Static demonstration copy, not a verified live count.
export const SOCIAL_PROOF_MESSAGE = '🔥 1,240 students joined this week';

export type SocialProofVariant = 'control' | typeof SOCIAL_PROOF_VARIANT;

export type SocialProofExperimentState =
    | { status: 'loading' }
    | { status: 'unavailable' }
    | { status: 'ready'; variant: SocialProofVariant; enrolled: boolean };

// Rendering branches on the variant key, never the flag value, so what is shown always matches the
// exposure the SDK records for that key.
export function resolveSocialProofExperiment(
    loadingState: LoadingState | undefined,
    flag: IFlagsmithFeature | null,
): SocialProofExperimentState {
    if (!loadingState || loadingState.error) {
        return { status: 'unavailable' };
    }
    if (loadingState.source !== 'SERVER') {
        return loadingState.isFetching || loadingState.isLoading ? { status: 'loading' } : { status: 'unavailable' };
    }
    if (!flag) {
        return { status: 'unavailable' };
    }
    const enrolled = flag.experiment?.inExperiment === true;
    const variant = enrolled && flag.variant === SOCIAL_PROOF_VARIANT ? SOCIAL_PROOF_VARIANT : 'control';
    return { status: 'ready', variant, enrolled };
}
