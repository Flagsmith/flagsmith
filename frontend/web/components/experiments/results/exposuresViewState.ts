import { ExperimentExposures, ExperimentStatus } from 'common/types/responses'
import { formatCountdown } from 'common/hooks/useCountdown'

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

export type RefreshLabel = { message: string; tone: 'muted' | 'danger' }

export const REFRESH_POLL_INTERVAL_MS = 10000
export const POLL_TIMEOUT_MS = 120000
export const DEFAULT_RETRY_AFTER_S = 300

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

export const getExposuresRefreshLabel = (
  retryAfter: number | null,
  isRefreshing: boolean,
): RefreshLabel | null => {
  if (retryAfter !== null) {
    return {
      message: `Refresh available in ${formatCountdown(retryAfter)}`,
      tone: 'muted',
    }
  }
  if (isRefreshing) {
    return {
      message: 'Computing… exposures will update automatically.',
      tone: 'muted',
    }
  }
  return null
}
