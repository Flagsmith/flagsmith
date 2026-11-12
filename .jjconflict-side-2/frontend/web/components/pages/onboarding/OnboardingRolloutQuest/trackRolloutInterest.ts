import flagsmith from '@flagsmith/flagsmith'

export const ROLLOUT_BETA_REQUESTED = 'rollout_beta_requested'
export const ROLLOUT_FEEDBACK_CLICKED = 'rollout_feedback_clicked'

type RolloutInterest = {
  email?: string
  organisation?: string
}

// The onboarding funnel events say an organisation wants this; this says who to
// reply to. Sent through flagsmith.trackEvent, same as the segment sources door.
const trackRolloutInterest = (
  event: string,
  { email, organisation }: RolloutInterest,
): void => {
  flagsmith.trackEvent(event, {
    metadata: {
      email,
      organisation,
      origin: 'onboarding-rollout-quest',
    },
  })
}

export default trackRolloutInterest
