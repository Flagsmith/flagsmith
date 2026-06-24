import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import { LineChart } from 'components/charts'
import ContentCard from 'components/base/grid/ContentCard'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import {
  useGetExperimentExposuresQuery,
  useRefreshExperimentExposuresMutation,
} from 'common/services/useExperiment'
import { Experiment, ExperimentExposures } from 'common/types/responses'
import {
  buildExposuresChartData,
  getHeadlineTotal,
  getVariantIdentities,
  getVariantTotals,
} from './derive'
import type { VariantTotal } from './derive'
import {
  POLL_TIMEOUT_MS,
  REFRESH_POLL_INTERVAL_MS,
  canRefreshExposures,
  deriveExposuresViewState,
} from './exposuresViewState'
import AsOfRefreshControl, { AsOfLabel } from './AsOfRefreshControl'
import './results.scss'

const buildLegendLabels = (totals: VariantTotal[]): Record<string, string> => {
  const labels: Record<string, string> = {}
  totals.forEach((t) => {
    labels[t.key] = `${t.name} (${t.total.toLocaleString()} - ${Math.round(
      t.share * 100,
    )}%)`
  })
  return labels
}

const parseRetryAfter = (err: unknown): number | null => {
  const fetchErr = err as {
    status?: number
    retryAfter?: number | null
  }
  if (fetchErr.status !== 429) return null
  if (fetchErr.retryAfter) return fetchErr.retryAfter
  return 300
}

const formatCountdown = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

type ExperimentExposuresPanelProps = {
  experiment: Experiment
  environmentId: string
  exposuresOverride?: ExperimentExposures
}

const REFRESH_DISABLED_COPY: Record<string, string> = {
  final: 'Refresh is disabled because the experiment is complete.',
  not_started: 'Start the experiment to compute exposures.',
}

const ExperimentExposuresPanel: FC<ExperimentExposuresPanelProps> = ({
  environmentId,
  experiment,
  exposuresOverride,
}) => {
  const [pollInterval, setPollInterval] = useState(0)
  const [refreshRequested, setRefreshRequested] = useState(false)
  const [pollStartedAt, setPollStartedAt] = useState<number | null>(null)
  const [retryAfter, setRetryAfter] = useState<number | null>(null)
  const { data: fetched } = useGetExperimentExposuresQuery(
    { environmentId, experimentId: experiment.id },
    {
      pollingInterval: pollInterval,
      refetchOnMountOrArgChange: true,
      skip: !!exposuresOverride,
    },
  )
  const exposures = exposuresOverride ?? fetched
  const [refresh, { isLoading: isSubmitting }] =
    useRefreshExperimentExposuresMutation()

  const viewState = deriveExposuresViewState(exposures)
  const availability = canRefreshExposures(experiment.status, exposures)
  const payload = exposures?.payload ?? null

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

  useEffect(() => {
    if (retryAfter === null || retryAfter <= 0) return
    const timer = setInterval(() => {
      setRetryAfter((prev) => {
        if (prev === null || prev <= 1) return null
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [retryAfter !== null]) // eslint-disable-line react-hooks/exhaustive-deps

  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )
  const chart = useMemo(
    () => (payload ? buildExposuresChartData(payload, identities) : null),
    [payload, identities],
  )
  const totals = useMemo(
    () => (payload ? getVariantTotals(payload, identities) : []),
    [payload, identities],
  )

  const isRefreshing = viewState.kind === 'refreshing' || isSubmitting
  const headline = payload ? getHeadlineTotal(payload) : 0
  const hasData = !!payload && headline > 0

  const handleRefresh = useCallback(async () => {
    const result = await refresh({
      environmentId,
      experimentId: experiment.id,
    })
    if ('error' in result && result.error) {
      const seconds = parseRetryAfter(result.error)
      if (seconds !== null) {
        setRetryAfter(seconds)
      } else {
        toast('Failed to refresh exposures', 'danger')
      }
    } else {
      setRefreshRequested(true)
      setPollStartedAt(Date.now())
    }
  }, [refresh, environmentId, experiment.id])

  const action = (
    <div className='d-flex flex-column align-items-end'>
      <AsOfRefreshControl
        asOf={exposures?.as_of ?? null}
        disabled={
          !availability.canRefresh || isRefreshing || retryAfter !== null
        }
        disabledReason={
          availability.reason
            ? REFRESH_DISABLED_COPY[availability.reason]
            : undefined
        }
        isRefreshing={isRefreshing && hasData}
        onRefresh={handleRefresh}
      />
      {retryAfter !== null && (
        <div className='text-muted fs-caption mt-1 text-end'>
          Computing, retry in {formatCountdown(retryAfter)}
        </div>
      )}
    </div>
  )

  const asOf = exposures?.as_of ?? null

  return (
    <ContentCard
      action={action}
      className='experiment-results__exposures-card'
      title='Enrollment over time'
    >
      {chart && hasData && (
        <>
          {isRefreshing && (
            <div className='text-muted fs-caption mb-2'>
              Computing… this will refresh automatically.
            </div>
          )}
          <LineChart
            colorMap={chart.colorMap}
            data={chart.points}
            height={260}
            series={chart.series}
            seriesLabels={buildLegendLabels(totals)}
            showLegend
          />
          <div className='fs-caption'>
            <AsOfLabel asOf={asOf} />
            {viewState.kind === 'error' && (
              <>
                <br />
                <span className='d-inline-flex align-items-center gap-1 text-danger'>
                  <Icon fill='#e53e3e' name='warning' width={14} />
                  The last exposure computation failed. Showing previously
                  computed data.
                </span>
              </>
            )}
          </div>
        </>
      )}

      {payload && !hasData && (
        <>
          <div className='text-muted text-center py-5'>
            No exposures collected yet.
          </div>
          <div className='d-flex justify-content-center gap-3 fs-caption mb-2'>
            {totals.map((t) => (
              <span key={t.key} className='d-flex align-items-center gap-1'>
                <span
                  style={{
                    background: t.colour,
                    borderRadius: '50%',
                    display: 'inline-block',
                    height: 8,
                    width: 8,
                  }}
                />
                {t.name}
              </span>
            ))}
          </div>
          <div className='fs-caption'>
            <AsOfLabel asOf={asOf} />
            {viewState.kind === 'error' && (
              <>
                <br />
                <span className='d-inline-flex align-items-center gap-1 text-danger'>
                  <Icon fill='#e53e3e' name='warning' width={14} />
                  The last exposure computation failed. Showing previously
                  computed data.
                </span>
              </>
            )}
          </div>
        </>
      )}

      {!payload && viewState.kind === 'error' && (
        <div className='d-flex align-items-center justify-content-center gap-1 text-danger fs-caption py-4'>
          <Icon fill='#e53e3e' name='warning' width={14} />
          The last exposure computation failed.
        </div>
      )}

      {!payload && viewState.kind !== 'error' && (
        <div className='text-muted text-center py-4'>
          {isRefreshing
            ? 'Computing exposures…'
            : 'No exposure data computed yet.'}
          {!isRefreshing && availability.canRefresh && (
            <div className='mt-2'>
              <Button onClick={handleRefresh} size='small' theme='secondary'>
                Compute now
              </Button>
            </div>
          )}
        </div>
      )}
    </ContentCard>
  )
}

export default ExperimentExposuresPanel
