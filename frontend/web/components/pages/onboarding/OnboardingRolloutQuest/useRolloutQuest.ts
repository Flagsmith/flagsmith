import React from 'react'
import API from 'project/api'
import Constants from 'common/constants'
import trackRolloutInterest, {
  ROLLOUT_BETA_REQUESTED,
  ROLLOUT_FEEDBACK_CLICKED,
} from './trackRolloutInterest'
import OnboardingRolloutQuest from './OnboardingRolloutQuest'

type UseRolloutQuest = {
  featureName: string
  /** Where "Create a rollout segment" ends up. */
  onContinue: () => void
  diagnosticIds: Record<string, unknown>
  /** Who to reply to when someone asks for access. */
  who: { email?: string; organisation?: string }
}

// The segment overrides tab alone shows none of the steps a rollout takes, so
// this opens first.
const useRolloutQuest = ({
  diagnosticIds,
  featureName,
  onContinue,
  who,
}: UseRolloutQuest): (() => void) => {
  const track = (event: { category: string; event: string }) =>
    API.trackEvent({ ...event, extra: diagnosticIds })

  return () => {
    track(Constants.events.ONBOARDING_ROLLOUT_VIEWED)
    openModal(
      // Matches the next-step card that opens it.
      'Gradual rollout',
      React.createElement(OnboardingRolloutQuest, {
        featureName,
        onContinue: () => {
          track(Constants.events.ONBOARDING_ROLLOUT_CONTINUED)
          closeModal()
          onContinue()
        },
        onDismiss: () => closeModal(),
        onFeedback: () => {
          track(Constants.events.ONBOARDING_ROLLOUT_FEEDBACK)
          trackRolloutInterest(ROLLOUT_FEEDBACK_CLICKED, who)
        },
        onNotifyMe: () => {
          track(Constants.events.ONBOARDING_ROLLOUT_NOTIFY_ME)
          trackRolloutInterest(ROLLOUT_BETA_REQUESTED, who)
        },
      }),
      'modal--wide',
    )
  }
}

export default useRolloutQuest
