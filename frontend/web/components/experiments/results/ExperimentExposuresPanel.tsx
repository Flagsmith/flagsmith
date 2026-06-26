import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import moment from 'moment'
import { LineChart } from 'components/charts'
import ContentCard from 'components/base/grid/ContentCard'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import useCountdown from 'common/hooks/useCountdown'
import { colorIconDanger } from 'common/theme/tokens'
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
  DEFAULT_RETRY_AFTER_S,
  POLL_TIMEOUT_MS,
  REFRESH_POLL_INTERVAL_MS,
  canRefreshExposures,
  deriveExposuresViewState,
  getExposuresRefreshLabel,
} from './exposuresViewState'
import RefreshControl from './RefreshControl'
import './results.scss'

const AsOfLabel: FC<{ asOf: string | null }> = ({ asOf }) => (
  <span className='text-muted fs-caption'>
    {asOf ? `As of ${moment.utc(asOf).format('D MMM YYYY, HH:mm')} UTC` : ''}
  </span>
)

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
  return DEFAULT_RETRY_AFTER_S
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
  const [retryAfter, startRetryCountdown] = useCountdown()
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

  const isRefreshing =
    refreshRequested || viewState.kind === 'refreshing' || isSubmitting
  const headline = payload ? getHeadlineTotal(payload) : 0
  const hasData = !!payload && headline > 0

  const handleRefresh = useCallback(async () => {
    setRefreshRequested(true)
    setPollStartedAt(Date.now())
    const result = await refresh({
      environmentId,
      experimentId: experiment.id,
    })
    if ('error' in result && result.error) {
      setRefreshRequested(false)
      setPollStartedAt(null)
      const seconds = parseRetryAfter(result.error)
      if (seconds !== null) {
        startRetryCountdown(seconds)
      } else {
        toast('Failed to refresh exposures', 'danger')
      }
    }
  }, [refresh, environmentId, experiment.id, startRetryCountdown])

  const refreshLabel = getExposuresRefreshLabel(retryAfter, isRefreshing)

  const action = (
    <RefreshControl
      disabled={!availability.canRefresh || retryAfter !== null}
      disabledReason={
        availability.reason
          ? REFRESH_DISABLED_COPY[availability.reason]
          : undefined
      }
      isRefreshing={isRefreshing}
      label={
        refreshLabel && (
          <span
            className={
              refreshLabel.tone === 'danger' ? 'text-danger' : undefined
            }
          >
            {refreshLabel.message}
          </span>
        )
      }
      onRefresh={handleRefresh}
    />
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
                  <Icon fill={colorIconDanger} name='warning' width={14} />
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
                  <Icon fill={colorIconDanger} name='warning' width={14} />
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
          <Icon fill={colorIconDanger} name='warning' width={14} />
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
