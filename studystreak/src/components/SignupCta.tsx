'use client';

import { useCallback, useEffect, useState } from 'react';
import { SOCIAL_PROOF_MESSAGE, SOCIAL_PROOF_VARIANT, type SocialProofExperimentState } from '@/lib/experiment';
import { useSocialProofExperiment } from '@/lib/use-social-proof-experiment';

export const FLAG_LOAD_TIMEOUT_MS = 3000;

const UNAVAILABLE: SocialProofExperimentState = { status: 'unavailable' };

export function SignupCta() {
    const [timedOut, setTimedOut] = useState(false);
    const handleTimeout = useCallback(() => setTimedOut(true), []);

    // Unmounting the experiment-aware CTA after a timeout stops useExperiment from recording an
    // exposure if flags arrive later, when this visitor has already seen the plain button.
    return timedOut ? <SignupCtaView experiment={UNAVAILABLE} /> : <ExperimentSignupCta onTimeout={handleTimeout} />;
}

function ExperimentSignupCta({ onTimeout }: { onTimeout: () => void }) {
    const experiment = useSocialProofExperiment();
    const isLoading = experiment.status === 'loading';

    useEffect(() => {
        if (!isLoading) {
            return;
        }
        const timer = setTimeout(onTimeout, FLAG_LOAD_TIMEOUT_MS);
        return () => clearTimeout(timer);
    }, [isLoading, onTimeout]);

    return <SignupCtaView experiment={experiment} />;
}

const BUTTON_SIZE = 'h-12 w-40 rounded-lg';

export function SignupCtaView({ experiment }: { experiment: SocialProofExperimentState }) {
    const isLoading = experiment.status === 'loading';
    const showSocialProof = experiment.status === 'ready' && experiment.variant === SOCIAL_PROOF_VARIANT;

    return (
        <div className="flex flex-col items-center gap-3 sm:items-start" aria-busy={isLoading} data-testid="signup-cta">
            {isLoading ? (
                <div
                    className={`${BUTTON_SIZE} bg-slate-200`}
                    aria-hidden="true"
                    data-testid="signup-cta-placeholder"
                />
            ) : (
                <button
                    type="button"
                    className={`${BUTTON_SIZE} bg-indigo-600 text-base font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600`}
                >
                    Sign Up
                </button>
            )}
            {/* The same fixed-height slot renders in every state, so the treatment never shifts the layout. */}
            <p className="h-6 text-sm font-medium text-slate-700" data-testid="social-proof-slot">
                {showSocialProof ? SOCIAL_PROOF_MESSAGE : null}
            </p>
        </div>
    );
}
