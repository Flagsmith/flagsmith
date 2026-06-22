import { ExperimentExposures, ExperimentStatus } from 'common/types/responses'

export type ExposuresViewState =
  | { kind: 'empty' }
  | { kind: 'loaded' }
  | { kind: 'refreshing' }
  | { kind: 'error'; staleAvailable: boolean }

export type RefreshReason = 'not_started' | 'final'
export type RefreshAvailability = {
  canRefresh: boolean
  reason?: RefreshReason
}

export const REFRESH_POLL_INTERVAL_MS = 10000
export const POLL_TIMEOUT_MS = 120000

const ms = (iso: string | null): number => (iso ? new Date(iso).getTime() : 0)

const isRefreshing = (e: ExperimentExposures): boolean => {
  const requested = ms(e.refresh_requested_at)
  return requested > 0 && requested > Math.max(ms(e.as_of), ms(e.last_error_at))
}

const hasError = (e: ExperimentExposures): boolean =>
  ms(e.last_error_at) > ms(e.as_of)

export const deriveExposuresViewState = (
  exposures: ExperimentExposures | null | undefined,
): ExposuresViewState => {
  if (!exposures) return { kind: 'empty' }
  if (isRefreshing(exposures)) return { kind: 'refreshing' }
  if (hasError(exposures)) {
    return { kind: 'error', staleAvailable: !!exposures.payload }
  }
  if (exposures.payload) return { kind: 'loaded' }
  return { kind: 'empty' }
}

export const canRefreshExposures = (
  status: ExperimentStatus,
  exposures: ExperimentExposures | null | undefined,
): RefreshAvailability => {
  if (status === 'created') return { canRefresh: false, reason: 'not_started' }
  if (status === 'completed' && exposures?.payload) {
    return { canRefresh: false, reason: 'final' }
  }
  return { canRefresh: true }
}
