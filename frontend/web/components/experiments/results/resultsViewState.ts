import {
  ExperimentBayesianResults,
  ExperimentStatus,
} from 'common/types/responses'
import { formatCountdown } from 'common/hooks/useCountdown'

export type ResultsViewState =
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

const isRefreshing = (r: ExperimentBayesianResults): boolean => {
  const requested = ms(r.refresh_requested_at)
  return requested > 0 && requested > Math.max(ms(r.as_of), ms(r.last_error_at))
}

const hasError = (r: ExperimentBayesianResults): boolean =>
  ms(r.last_error_at) > ms(r.as_of)

export const deriveResultsViewState = (
  results: ExperimentBayesianResults | null | undefined,
): ResultsViewState => {
  if (!results) return { kind: 'empty' }
  if (isRefreshing(results)) return { kind: 'refreshing' }
  if (hasError(results)) {
    return { kind: 'error', staleAvailable: !!results.payload }
  }
  if (results.payload) return { kind: 'loaded' }
  return { kind: 'empty' }
}

export const canRefreshResults = (
  status: ExperimentStatus,
  results: ExperimentBayesianResults | null | undefined,
): RefreshAvailability => {
  if (status === 'created') return { canRefresh: false, reason: 'not_started' }
  if (results?.is_final) return { canRefresh: false, reason: 'final' }
  return { canRefresh: true }
}

export const getResultsRefreshLabel = (
  retryAfter: number | null,
  isRefreshing: boolean,
  viewState: ResultsViewState,
): RefreshLabel | null => {
  if (retryAfter !== null) {
    return {
      message: `Computing… retry in ${formatCountdown(retryAfter)}`,
      tone: 'muted',
    }
  }
  if (isRefreshing) {
    return {
      message: 'Computing… results will update automatically.',
      tone: 'muted',
    }
  }
  if (viewState.kind === 'error') {
    return { message: 'The last results computation failed.', tone: 'danger' }
  }
  return null
}
