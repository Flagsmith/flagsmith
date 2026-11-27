import type { IFlagsmithFeature, LoadingState } from '@flagsmith/flagsmith/types';

export const SOCIAL_PROOF_FLAG = 'study_streak_social_proof';
export const SOCIAL_PROOF_VARIANT = 'social_proof';
export const SIGNUP_CLICKED_EVENT = 'signup_clicked';
export const SIGNED_UP_EVENT = 'signed_up';
// Static demonstration copy, not a verified live count.
export const SOCIAL_PROOF_MESSAGE = '🔥 1,240 students joined this week';

export type SocialProofVariant = 'control' | typeof SOCIAL_PROOF_VARIANT;

export type SocialProofExperimentState =
    | { status: 'loading' }
    | { status: 'unavailable'; reason?: 'unknown_variant' }
    | { status: 'ready'; variant: SocialProofVariant; enrolled: boolean };

const isKnownVariant = (variant: unknown): variant is SocialProofVariant =>
    variant === 'control' || variant === SOCIAL_PROOF_VARIANT;

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
        // NONE (without an error) means the SDK has not finished initialising yet, even before it starts fetching.
        // SignupCta's timeout ends this state if flags never arrive.
        const pending = loadingState.isFetching || loadingState.isLoading || loadingState.source === 'NONE';
        return pending ? { status: 'loading' } : { status: 'unavailable' };
    }
    if (!flag) {
        return { status: 'unavailable' };
    }
    // The SDK records no exposure for a disabled flag, so a disabled flag never renders an assigned variant.
    const enrolled = flag.enabled && flag.experiment?.inExperiment === true;
    if (!enrolled) {
        return { status: 'ready', variant: 'control', enrolled: false };
    }
    // An unrecognised key (such as the dashboard's default "Variant_1") is a misconfiguration. It is not shown as
    // control, which would attribute control content to another arm; the CTA falls back and tracks no clicks.
    if (!isKnownVariant(flag.variant)) {
        return { status: 'unavailable', reason: 'unknown_variant' };
    }
    return { status: 'ready', variant: flag.variant, enrolled: true };
}
