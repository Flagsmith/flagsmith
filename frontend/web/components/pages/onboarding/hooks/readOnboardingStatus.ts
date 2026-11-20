import { Res } from 'common/types/responses'

export type OnboardingStatusReading = 'connected' | 'listening' | 'unknown'

// A "not evaluated yet" counts only when fetched during this visit: RTK Query
// can serve a cached one from an earlier visit on remount.
export const readOnboardingStatus = (
  data: Res['environmentOnboardingStatus'] | undefined,
  fetchedAt: number | undefined,
  mountedAt: number,
): OnboardingStatusReading => {
  if (!data) return 'unknown'
  if (data.first_evaluated_at) return 'connected'
  return fetchedAt !== undefined && fetchedAt >= mountedAt
    ? 'listening'
    : 'unknown'
}
