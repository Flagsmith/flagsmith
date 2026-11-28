import { useExperiment, useFlagsmithLoading } from '@flagsmith/flagsmith/react';
import { useEffect } from 'react';
import { resolveSocialProofExperiment, SOCIAL_PROOF_FLAG, type SocialProofExperimentState } from '@/lib/experiment';

// useExperiment records the exposure only for enrolled identities with flags loaded from the server,
// so call this hook in the component that renders the variant.
export function useSocialProofExperiment(): SocialProofExperimentState {
    const loadingState = useFlagsmithLoading();
    const flag = useExperiment(SOCIAL_PROOF_FLAG);
    const state = resolveSocialProofExperiment(loadingState, flag);
    const unknownVariant = state.status === 'unavailable' && state.reason === 'unknown_variant';

    useEffect(() => {
        if (unknownVariant) {
            console.error(
                `"${SOCIAL_PROOF_FLAG}" returned an unknown variant key. Expected "control" or "social_proof"; check the variation key in Flagsmith.`,
            );
        }
    }, [unknownVariant]);

    return state;
}
