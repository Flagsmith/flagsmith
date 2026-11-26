import { useExperiment, useFlagsmithLoading } from '@flagsmith/flagsmith/react';
import { resolveSocialProofExperiment, SOCIAL_PROOF_FLAG, type SocialProofExperimentState } from '@/lib/experiment';

// useExperiment records the exposure only for enrolled identities with flags loaded from the server,
// so call this hook in the component that renders the variant.
export function useSocialProofExperiment(): SocialProofExperimentState {
    const loadingState = useFlagsmithLoading();
    const flag = useExperiment(SOCIAL_PROOF_FLAG);
    return resolveSocialProofExperiment(loadingState, flag);
}
