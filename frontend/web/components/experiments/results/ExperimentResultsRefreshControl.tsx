import { FC, useCallback, useEffect, useState } from 'react'
import useCountdown from 'common/hooks/useCountdown'
import {
  useGetExperimentBayesianResultsQuery,
  useRefreshExperimentBayesianResultsMutation,
} from 'common/services/useExperiment'
import { ExperimentStatus } from 'common/types/responses'
import RefreshControl from './RefreshControl'
import {
  DEFAULT_RETRY_AFTER_S,
  POLL_TIMEOUT_MS,
  REFRESH_POLL_INTERVAL_MS,
  canRefreshResults,
  deriveResultsViewState,
  getResultsRefreshLabel,
} from './resultsViewState'

const parseRetryAfter = (err: unknown): number | null => {
  const fetchErr = err as {
    status?: number
    retryAfter?: number | null
  }
  if (fetchErr.status !== 429) return null
  if (fetchErr.retryAfter) return fetchErr.retryAfter
  return DEFAULT_RETRY_AFTER_S
}

type ExperimentResultsRefreshControlProps = {
  environmentId: string
  experimentId: number
  status: ExperimentStatus
}

const REFRESH_DISABLED_COPY: Record<string, string> = {
  final: 'Refresh is disabled because the experiment is complete.',
  not_started: 'Start the experiment to compute results.',
}

const ExperimentResultsRefreshControl: FC<
  ExperimentResultsRefreshControlProps
> = ({ environmentId, experimentId, status }) => {
  const [pollInterval, setPollInterval] = useState(0)
  const [refreshRequested, setRefreshRequested] = useState(false)
  const [pollStartedAt, setPollStartedAt] = useState<number | null>(null)
  const [retryAfter, startRetryCountdown] = useCountdown()

  const { data: results } = useGetExperimentBayesianResultsQuery(
    { environmentId, experimentId },
    { pollingInterval: pollInterval },
  )
  const [refresh, { isLoading: isSubmitting }] =
    useRefreshExperimentBayesianResultsMutation()

  const viewState = deriveResultsViewState(results)
  const availability = canRefreshResults(status, results)

  const pollTimedOut =
    pollStartedAt !== null && Date.now() - pollStartedAt > POLL_TIMEOUT_MS
  const shouldPoll =
    !pollTimedOut && (viewState.kind === 'refreshing' || refreshRequested)
  const nextPollInterval = shouldPoll ? REFRESH_POLL_INTERVAL_MS : 0
  useEffect(() => {
    setPollInterval(nextPollInterval)
  }, [nextPollInterval])

  useEffect(() => {
    if (viewState.kind === 'loaded' || viewState.kind === 'error') {
      setRefreshRequested(false)
      setPollStartedAt(null)
    }
  }, [viewState.kind])

  useEffect(() => {
    if (pollTimedOut) {
      setRefreshRequested(false)
      setPollStartedAt(null)
    }
  }, [pollTimedOut])

  const isRefreshing =
    refreshRequested || viewState.kind === 'refreshing' || isSubmitting

  const handleRefresh = useCallback(async () => {
    setRefreshRequested(true)
    setPollStartedAt(Date.now())
    const result = await refresh({ environmentId, experimentId })
    if ('error' in result && result.error) {
      setRefreshRequested(false)
      setPollStartedAt(null)
      const seconds = parseRetryAfter(result.error)
      if (seconds !== null) {
        startRetryCountdown(seconds)
      } else {
        toast('Failed to refresh results', 'danger')
      }
    }
  }, [refresh, environmentId, experimentId, startRetryCountdown])

  const label = getResultsRefreshLabel(retryAfter, isRefreshing, viewState)

  return (
    <RefreshControl
      disabled={!availability.canRefresh || retryAfter !== null}
      disabledReason={
        availability.reason
          ? REFRESH_DISABLED_COPY[availability.reason]
          : undefined
      }
      isRefreshing={isRefreshing}
      label={
        label && (
          <span className={label.tone === 'danger' ? 'text-danger' : undefined}>
            {label.message}
          </span>
        )
      }
      onRefresh={handleRefresh}
    >
      Refresh results
    </RefreshControl>
  )
}

export default ExperimentResultsRefreshControl
