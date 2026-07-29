import { useEffect, useState } from 'react'
import { useGetEnvironmentOnboardingStatusQuery } from 'common/services/useEnvironmentOnboardingStatus'

export type OnboardingConnectionStatus = 'listening' | 'connected'

// Edge reports the first evaluation asynchronously after the SDK's first
// request, so the flip isn't instant — poll until it lands.
const POLL_INTERVAL_MS = 3000

// Connection status for the verify console, driven by the real first-evaluation
// signal: Edge reports the first SDK evaluation to Core, exposed at
// GET environments/{key}/onboarding-status/. `first_evaluated_at` flips from
// null to a timestamp once received; it never reverts, so we stop polling then.
export const useOnboardingConnection = (
  environmentKey: string,
): OnboardingConnectionStatus => {
  const [firstEvaluated, setFirstEvaluated] = useState(false)

  const { data } = useGetEnvironmentOnboardingStatusQuery(
    { environmentKey },
    {
      pollingInterval: POLL_INTERVAL_MS,
      skip: firstEvaluated || !environmentKey,
    },
  )

  useEffect(() => {
    if (data?.first_evaluated_at) {
      setFirstEvaluated(true)
    }
  }, [data])

  return firstEvaluated ? 'connected' : 'listening'
}
