import { FC, useCallback, useEffect, useState } from 'react'
import useCountdown from 'common/hooks/useCountdown'
import {
  useGetExperimentBayesianResultsQuery,
  useGetExperimentExposuresQuery,
  useRefreshExperimentBayesianResultsMutation,
  useRefreshExperimentExposuresMutation,
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
import { deriveExposuresViewState } from './exposuresViewState'

const parseRetryAfter = (err: unknown): number | null => {
  const fetchErr = err as {
    status?: number
    retryAfter?: number | null
  }
  if (fetchErr.status !== 429) return null
  if (fetchErr.retryAfter) return fetchErr.retryAfter
  return DEFAULT_RETRY_AFTER_S
}

const getMaxRetryAfter = (errors: unknown[]): number | null => {
  let max: number | null = null
  for (const err of errors) {
    const seconds = parseRetryAfter(err)
    if (seconds !== null && (max === null || seconds > max)) {
      max = seconds
    }
  }
  return max
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
  const { data: exposures } = useGetExperimentExposuresQuery(
    { environmentId, experimentId },
    { pollingInterval: pollInterval },
  )
  const [refreshResults, { isLoading: isSubmittingResults }] =
    useRefreshExperimentBayesianResultsMutation()
  const [refreshExposures, { isLoading: isSubmittingExposures }] =
    useRefreshExperimentExposuresMutation()

  const resultsViewState = deriveResultsViewState(results)
  const exposuresViewState = deriveExposuresViewState(exposures)
  const availability = canRefreshResults(status, results)

  const eitherRefreshing =
    resultsViewState.kind === 'refreshing' ||
    exposuresViewState.kind === 'refreshing'
  const bothSettled =
    resultsViewState.kind !== 'refreshing' &&
    exposuresViewState.kind !== 'refreshing'

  const pollTimedOut =
    pollStartedAt !== null && Date.now() - pollStartedAt > POLL_TIMEOUT_MS
  const shouldPoll = !pollTimedOut && (eitherRefreshing || refreshRequested)
  const nextPollInterval = shouldPoll ? REFRESH_POLL_INTERVAL_MS : 0
  useEffect(() => {
    setPollInterval(nextPollInterval)
  }, [nextPollInterval])

  useEffect(() => {
    if (refreshRequested && bothSettled) {
      setRefreshRequested(false)
      setPollStartedAt(null)
    }
  }, [refreshRequested, bothSettled])

  useEffect(() => {
    if (pollTimedOut) {
      setRefreshRequested(false)
      setPollStartedAt(null)
    }
  }, [pollTimedOut])

  const isRefreshing =
    refreshRequested ||
    eitherRefreshing ||
    isSubmittingResults ||
    isSubmittingExposures

  const handleRefresh = useCallback(async () => {
    setRefreshRequested(true)
    setPollStartedAt(Date.now())
    const [resultsResult, exposuresResult] = await Promise.all([
      refreshResults({ environmentId, experimentId }),
      refreshExposures({ environmentId, experimentId }),
    ])
    const errors: unknown[] = []
    if ('error' in resultsResult && resultsResult.error) {
      errors.push(resultsResult.error)
    }
    if ('error' in exposuresResult && exposuresResult.error) {
      errors.push(exposuresResult.error)
    }
    if (errors.length > 0) {
      const seconds = getMaxRetryAfter(errors)
      const hasNonRetryable = errors.some((e) => parseRetryAfter(e) === null)
      if (hasNonRetryable) {
        toast('Failed to refresh experiment data', 'danger')
      }
      if (seconds !== null) {
        startRetryCountdown(seconds)
      } else {
        setRefreshRequested(false)
        setPollStartedAt(null)
      }
    }
  }, [
    refreshResults,
    refreshExposures,
    environmentId,
    experimentId,
    startRetryCountdown,
  ])

  const label = getResultsRefreshLabel(
    retryAfter,
    isRefreshing,
    resultsViewState,
  )

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
      Refresh
    </RefreshControl>
  )
}

export default ExperimentResultsRefreshControl
