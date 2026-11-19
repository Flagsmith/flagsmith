import { useEffect, useState } from 'react'
import { useGetEnvironmentOnboardingStatusQuery } from 'common/services/useEnvironmentOnboardingStatus'

export type OnboardingConnectionStatus = 'listening' | 'connected'

export type OnboardingConnection = {
  status: OnboardingConnectionStatus
  sdkLabel: string | null // null until the signal lands, or if unidentified
  // True when a poll saw no evaluation first, so it happened on this page.
  connectedOnPage: boolean
}

const POLL_INTERVAL_MS = 5000

const UNIDENTIFIED_SDK = 'unknown' // what Core sends for an unknown user agent

// Polls onboarding-status/ until Core reports the first SDK evaluation.
export const useOnboardingConnection = (
  environmentKey: string,
): OnboardingConnection => {
  // Kept in state, not read from `data`: the query is skipped once the signal
  // lands, and a skipped query has no data to read.
  const [firstEvaluation, setFirstEvaluation] = useState<{
    sdkLabel: string | null
    connectedOnPage: boolean
  } | null>(null)
  const [sawListening, setSawListening] = useState(false)

  const { data } = useGetEnvironmentOnboardingStatusQuery(
    { environmentKey },
    {
      pollingInterval: POLL_INTERVAL_MS,
      skip: !!firstEvaluation || !environmentKey,
      skipPollingIfUnfocused: true, // pauses when hidden; visibilitychange, not blur
    },
  )

  useEffect(() => {
    if (!data) return
    if (!data.first_evaluated_at) {
      setSawListening(true)
      return
    }
    const label = data.first_evaluated_sdk_label
    setFirstEvaluation({
      connectedOnPage: sawListening,
      sdkLabel: label && label !== UNIDENTIFIED_SDK ? label : null,
    })
  }, [data, sawListening])

  return {
    connectedOnPage: firstEvaluation?.connectedOnPage ?? false,
    sdkLabel: firstEvaluation?.sdkLabel ?? null,
    status: firstEvaluation ? 'connected' : 'listening',
  }
}
