import { FC, useEffect, useMemo, useState } from 'react'
import { LineChart } from 'components/charts'
import ContentCard from 'components/base/grid/ContentCard'
import Button from 'components/base/forms/Button'
import {
  useGetExperimentExposuresQuery,
  useRefreshExperimentExposuresMutation,
} from 'common/services/useExperiment'
import { Experiment } from 'common/types/responses'
import {
  buildExposuresChartData,
  getVariantIdentities,
  getVariantTotals,
} from './derive'
import type { VariantTotal } from './derive'
import {
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

type ExperimentExposuresPanelProps = {
  experiment: Experiment
  environmentId: string
}

const REFRESH_DISABLED_COPY: Record<string, string> = {
  final: 'Refresh is disabled because the experiment is complete.',
  not_started: 'Start the experiment to compute exposures.',
}

const ExperimentExposuresPanel: FC<ExperimentExposuresPanelProps> = ({
  environmentId,
  experiment,
}) => {
  const [pollInterval, setPollInterval] = useState(0)
  const [refreshRequested, setRefreshRequested] = useState(false)
  const { data: exposures } = useGetExperimentExposuresQuery(
    { environmentId, experimentId: experiment.id },
    {
      pollingInterval: pollInterval,
      refetchOnMountOrArgChange: true,
    },
  )
  const [refresh, { isLoading: isSubmitting }] =
    useRefreshExperimentExposuresMutation()

  const viewState = deriveExposuresViewState(exposures)
  const availability = canRefreshExposures(experiment.status, exposures)
  const payload = exposures?.payload ?? null

  const shouldPoll =
    viewState.kind === 'refreshing' || (refreshRequested && !payload)
  const nextPollInterval = shouldPoll ? REFRESH_POLL_INTERVAL_MS : 0
  useEffect(() => {
    setPollInterval(nextPollInterval)
  }, [nextPollInterval])

  useEffect(() => {
    if (viewState.kind === 'loaded' || viewState.kind === 'error') {
      setRefreshRequested(false)
    }
  }, [viewState.kind])

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
  const hasData = !!payload

  const handleRefresh = async () => {
    try {
      await refresh({ environmentId, experimentId: experiment.id }).unwrap()
      setRefreshRequested(true)
    } catch {
      toast('Failed to refresh exposures', 'danger')
    }
  }

  const action = (
    <AsOfRefreshControl
      asOf={exposures?.as_of ?? null}
      disabled={!availability.canRefresh || isRefreshing}
      disabledReason={
        availability.reason
          ? REFRESH_DISABLED_COPY[availability.reason]
          : undefined
      }
      isRefreshing={isRefreshing && hasData}
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
      {viewState.kind === 'error' && (
        <div className='alert alert-warning'>
          The last refresh failed.
          {viewState.staleAvailable
            ? ' Showing the previously computed data.'
            : ''}
        </div>
      )}

      {chart ? (
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
          <AsOfLabel asOf={asOf} />
        </>
      ) : (
        viewState.kind !== 'error' && (
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
        )
      )}
    </ContentCard>
  )
}

export default ExperimentExposuresPanel
