import flagsmith from '@flagsmith/flagsmith'

export const ROLLOUT_BETA_REQUESTED = 'rollout_beta_requested'
export const ROLLOUT_FEEDBACK_CLICKED = 'rollout_feedback_clicked'

type RolloutInterest = {
  email?: string
  organisation?: string
}

/**
 * Interest in the door, reported where the other fake doors report and
 * carrying who asked. The onboarding funnel events record that an
 * organisation wants this; these record who to reply to. Same shape as the
 * segment sources door.
 *
 * Takes who rather than reading it, so the caller supplies it from the queries
 * it already holds.
 */
const trackRolloutInterest = (
  event: string,
  { email, organisation }: RolloutInterest,
): void => {
  flagsmith.trackEvent(event, {
    metadata: {
      email,
      organisation,
      source: 'onboarding-rollout-quest',
    },
  })
}

export default trackRolloutInterest
