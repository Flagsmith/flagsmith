import { useEffect, useState } from 'react'
import { useGetEnvironmentOnboardingStatusQuery } from 'common/services/useEnvironmentOnboardingStatus'

export type OnboardingConnectionStatus = 'listening' | 'connected'

export type OnboardingConnection = {
  status: OnboardingConnectionStatus
  sdkLabel: string | null // null until the signal lands, or if unidentified
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
  } | null>(null)

  const { data } = useGetEnvironmentOnboardingStatusQuery(
    { environmentKey },
    {
      pollingInterval: POLL_INTERVAL_MS,
      skip: !!firstEvaluation || !environmentKey,
      skipPollingIfUnfocused: true, // pauses when hidden; visibilitychange, not blur
    },
  )

  useEffect(() => {
    if (!data?.first_evaluated_at) return
    const label = data.first_evaluated_sdk_label
    setFirstEvaluation({
      sdkLabel: label && label !== UNIDENTIFIED_SDK ? label : null,
    })
  }, [data])

  return {
    sdkLabel: firstEvaluation?.sdkLabel ?? null,
    status: firstEvaluation ? 'connected' : 'listening',
  }
}
