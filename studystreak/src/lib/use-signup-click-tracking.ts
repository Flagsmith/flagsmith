import { FlagsmithContext } from '@flagsmith/flagsmith/react';
import { useCallback, useContext, useEffect, useLayoutEffect, useMemo } from 'react';
import { claimFirstSignupClickAcrossTabs, createBrowserStore, recordFirstExposure } from '@/lib/exposure-clock';
import { SIGNUP_CLICKED_EVENT, type SocialProofExperimentState } from '@/lib/experiment';

// A layout effect runs before the browser paints, so before the button can receive a click. On the server it would
// warn and do nothing, so the passive effect is used there instead.
const useBeforePaintEffect = typeof window === 'undefined' ? useEffect : useLayoutEffect;

// Records the first exposure time and returns a click handler that sends signup_clicked once per
// visitor, valued in seconds since that exposure. Visitors who were never exposed send nothing.
export function useSignupClickTracking(experiment: SocialProofExperimentState): () => void {
    const flagsmith = useContext(FlagsmithContext);
    const visitorId = flagsmith?.getContext().identity?.identifier ?? null;
    const exposed = experiment.status === 'ready' && experiment.enrolled;
    const store = useMemo(() => createBrowserStore(), []);

    useBeforePaintEffect(() => {
        if (exposed && visitorId) {
            recordFirstExposure(store, visitorId);
        }
    }, [exposed, visitorId, store]);

    return useCallback(() => {
        if (!flagsmith || !exposed || !visitorId) {
            return;
        }
        // If the click somehow arrives before the exposure was stored, store it now rather than drop the click.
        recordFirstExposure(store, visitorId);
        void claimFirstSignupClickAcrossTabs(store, visitorId).then((secondsSinceExposure) => {
            if (secondsSinceExposure === null) {
                return;
            }
            flagsmith.trackEvent(SIGNUP_CLICKED_EVENT, { identifier: visitorId, value: secondsSinceExposure });
            void flagsmith.flushEvents();
        });
    }, [flagsmith, exposed, visitorId, store]);
}
