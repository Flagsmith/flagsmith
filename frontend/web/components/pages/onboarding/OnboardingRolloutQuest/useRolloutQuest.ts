import { useEffect } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import API from 'project/api'
import Constants from 'common/constants'
import trackRolloutInterest, {
  ROLLOUT_BETA_REQUESTED,
  ROLLOUT_FEEDBACK_CLICKED,
} from './trackRolloutInterest'
import { OnboardingRolloutQuestProps } from './OnboardingRolloutQuest'

type UseRolloutQuest = {
  featureName: string
  /** Where "Create a rollout segment" ends up. */
  onContinue: () => void
  /** Onboarding funnel context, as the other onboarding events send it. */
  diagnosticIds: Record<string, unknown>
  /** Who to reply to when someone asks for access. */
  who: { email?: string; organisation?: string }
}

/**
 * The rollout quest's own routing and analytics, so the flow only has to ask
 * whether it is open.
 *
 * Rollout is the one quest with a screen of its own: the segment overrides tab
 * alone explains none of the steps a rollout takes. The rest still go straight
 * to their config. The open quest lives in the URL, so refresh and back both
 * behave.
 */
const useRolloutQuest = ({
  diagnosticIds,
  featureName,
  onContinue,
  who,
}: UseRolloutQuest): {
  isOpen: boolean
  open: () => void
  props: OnboardingRolloutQuestProps
} => {
  const history = useHistory()
  const location = useLocation()
  const isOpen = new URLSearchParams(location.search).get('quest') === 'rollout'

  const track = (event: { category: string; event: string }) =>
    API.trackEvent({ ...event, extra: diagnosticIds })

  useEffect(() => {
    if (!isOpen) return
    API.trackEvent({
      ...Constants.events.ONBOARDING_ROLLOUT_VIEWED,
      extra: diagnosticIds,
    })
    // Once per opening, not on every id settling.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  return {
    isOpen,
    open: () => history.push('/getting-started?quest=rollout'),
    props: {
      featureName,
      onContinue: () => {
        track(Constants.events.ONBOARDING_ROLLOUT_CONTINUED)
        onContinue()
      },
      onDismiss: () => history.push('/getting-started'),
      onFeedback: () => {
        track(Constants.events.ONBOARDING_ROLLOUT_FEEDBACK)
        trackRolloutInterest(ROLLOUT_FEEDBACK_CLICKED, who)
      },
      onNotifyMe: () => {
        track(Constants.events.ONBOARDING_ROLLOUT_NOTIFY_ME)
        trackRolloutInterest(ROLLOUT_BETA_REQUESTED, who)
      },
    },
  }
}

export default useRolloutQuest
