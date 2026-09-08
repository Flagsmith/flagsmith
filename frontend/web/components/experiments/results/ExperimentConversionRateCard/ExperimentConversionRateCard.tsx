import { FC, useMemo } from 'react'
import moment from 'moment'
import { LineChart } from 'components/charts'
import ContentCard from 'components/base/grid/ContentCard'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  getMetricResult,
  getVariantIdentities,
} from 'components/experiments/results/derive'
import { buildConversionChartData } from 'components/experiments/results/deriveConversionRate'

type ExperimentConversionRateCardProps = {
  experiment: Experiment
  results?: BayesianResultsSummary
  asOf: string | null
}

const ExperimentConversionRateCard: FC<ExperimentConversionRateCardProps> = ({
  asOf,
  experiment,
  results,
}) => {
  const metric = getPrimaryMetric(experiment)
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )
  const chart = useMemo(
    () =>
      metric && results
        ? buildConversionChartData(results, metric.metric, identities)
        : null,
    [metric, results, identities],
  )

  // Hidden entirely when no conversions can be charted: value metrics, and
  // payloads stored before the backend shipped the timeseries.
  if (!metric || !results || !chart) return null

  const conversions = getMetricResult(
    results,
    metric.metric,
  )?.conversions_timeseries
  const hasConversions = !!conversions && conversions.points.length > 0

  return (
    <ContentCard
      action={
        hasConversions ? (
          // Single metric today — disabled until multi-metric ships.
          <div style={{ minWidth: 180 }}>
            <Select
              isDisabled
              size='select-sm'
              value={{ label: metric.metric_name, value: metric.metric }}
              options={[{ label: metric.metric_name, value: metric.metric }]}
            />
          </div>
        ) : undefined
      }
      title='Conversions over time'
    >
      {hasConversions ? (
        <>
          <LineChart
            colorMap={chart.colorMap}
            data={chart.points}
            height={260}
            series={chart.series}
            seriesLabels={chart.seriesLabels}
            showLegend
          />
          <span className='text-muted fs-caption'>
            {asOf
              ? `As of ${moment.utc(asOf).format('D MMM YYYY, HH:mm')} UTC`
              : ''}
          </span>
        </>
      ) : (
        <div className='text-muted text-center py-5'>
          No conversions recorded yet.
        </div>
      )}
    </ContentCard>
  )
}

export default ExperimentConversionRateCard
