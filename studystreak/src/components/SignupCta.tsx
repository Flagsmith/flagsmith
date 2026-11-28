'use client';

import { useCallback, useEffect, useState } from 'react';
import { SOCIAL_PROOF_MESSAGE, SOCIAL_PROOF_VARIANT, type SocialProofExperimentState } from '@/lib/experiment';
import { useSignupClickTracking } from '@/lib/use-signup-click-tracking';
import { useSocialProofExperiment } from '@/lib/use-social-proof-experiment';
import { SignupDialog } from './SignupDialog';

export const FLAG_LOAD_TIMEOUT_MS = 3000;

const UNAVAILABLE: SocialProofExperimentState = { status: 'unavailable' };

export function SignupCta() {
    const [timedOut, setTimedOut] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const handleTimeout = useCallback(() => setTimedOut(true), []);
    const openDialog = useCallback(() => setDialogOpen(true), []);
    const closeDialog = useCallback(() => setDialogOpen(false), []);

    return (
        <>
            {/* Unmounting the experiment-aware CTA after a timeout stops useExperiment from recording an
                exposure if flags arrive later, when this visitor has already seen the plain button. */}
            {timedOut ? (
                <SignupCtaView experiment={UNAVAILABLE} onSignUp={openDialog} />
            ) : (
                <ExperimentSignupCta onTimeout={handleTimeout} onSignUp={openDialog} />
            )}
            <SignupDialog open={dialogOpen} onClose={closeDialog} />
        </>
    );
}

function ExperimentSignupCta({ onTimeout, onSignUp }: { onTimeout: () => void; onSignUp: () => void }) {
    const experiment = useSocialProofExperiment();
    const trackSignupClick = useSignupClickTracking(experiment);
    const isLoading = experiment.status === 'loading';

    useEffect(() => {
        if (!isLoading) {
            return;
        }
        const timer = setTimeout(onTimeout, FLAG_LOAD_TIMEOUT_MS);
        return () => clearTimeout(timer);
    }, [isLoading, onTimeout]);

    const handleSignUp = useCallback(() => {
        trackSignupClick();
        onSignUp();
    }, [trackSignupClick, onSignUp]);

    return <SignupCtaView experiment={experiment} onSignUp={handleSignUp} />;
}

const BUTTON_SIZE = 'h-12 w-40 rounded-lg';

export function SignupCtaView({
    experiment,
    onSignUp,
}: {
    experiment: SocialProofExperimentState;
    onSignUp: () => void;
}) {
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
                    onClick={onSignUp}
                    aria-haspopup="dialog"
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
