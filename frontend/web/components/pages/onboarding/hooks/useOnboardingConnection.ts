import { useEffect, useState } from 'react'
import { useGetEnvironmentOnboardingStatusQuery } from 'common/services/useEnvironmentOnboardingStatus'

export type OnboardingConnectionStatus = 'listening' | 'connected'

export type OnboardingConnection = {
  status: OnboardingConnectionStatus
  // Which SDK reported the first evaluation, e.g. 'flagsmith-python-sdk'. Null
  // until the signal lands, and also when Core could not identify the SDK from
  // the user agent (it sends 'unknown', which is nothing to show a user).
  sdkLabel: string | null
}

// Edge reports the first evaluation asynchronously after the SDK's first
// request, so the flip isn't instant — poll until it lands.
const POLL_INTERVAL_MS = 3000

const UNIDENTIFIED_SDK = 'unknown'

// Connection status for the verify console, driven by the real first-evaluation
// signal: Edge reports the first SDK evaluation to Core, exposed at
// GET environments/{key}/onboarding-status/. `first_evaluated_at` flips from
// null to a timestamp once received; it never reverts, so we stop polling then.
// The signal is latched into state because skipping the query drops `data`.
export const useOnboardingConnection = (
  environmentKey: string,
): OnboardingConnection => {
  const [firstEvaluation, setFirstEvaluation] = useState<{
    sdkLabel: string | null
  } | null>(null)

  const { data } = useGetEnvironmentOnboardingStatusQuery(
    { environmentKey },
    {
      pollingInterval: POLL_INTERVAL_MS,
      skip: !!firstEvaluation || !environmentKey,
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
