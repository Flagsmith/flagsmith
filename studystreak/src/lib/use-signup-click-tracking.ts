import { FlagsmithContext } from '@flagsmith/flagsmith/react';
import { useCallback, useContext, useEffect, useMemo } from 'react';
import { claimFirstSignupClick, createBrowserStore, recordFirstExposure } from '@/lib/exposure-clock';
import { SIGNUP_CLICKED_EVENT, type SocialProofExperimentState } from '@/lib/experiment';

// Records the first exposure time and returns a click handler that sends signup_clicked once per
// visitor, valued in seconds since that exposure. Visitors who were never exposed send nothing.
export function useSignupClickTracking(experiment: SocialProofExperimentState): () => void {
    const flagsmith = useContext(FlagsmithContext);
    const visitorId = flagsmith?.getContext().identity?.identifier ?? null;
    const exposed = experiment.status === 'ready' && experiment.enrolled;
    const store = useMemo(() => createBrowserStore(), []);

    useEffect(() => {
        if (exposed && visitorId) {
            recordFirstExposure(store, visitorId);
        }
    }, [exposed, visitorId, store]);

    return useCallback(() => {
        if (!flagsmith || !exposed || !visitorId) {
            return;
        }
        const secondsSinceExposure = claimFirstSignupClick(store, visitorId);
        if (secondsSinceExposure === null) {
            return;
        }
        flagsmith.trackEvent(SIGNUP_CLICKED_EVENT, { identifier: visitorId, value: secondsSinceExposure });
        void flagsmith.flushEvents();
    }, [flagsmith, exposed, visitorId, store]);
}
