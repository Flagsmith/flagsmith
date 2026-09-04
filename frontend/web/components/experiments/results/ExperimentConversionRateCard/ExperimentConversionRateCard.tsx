import { FC, useCallback, useMemo, useState } from 'react'
import moment from 'moment'
import { BarChart } from 'components/charts'
import ContentCard from 'components/base/grid/ContentCard'
import InlinePillToggle from 'components/base/forms/InlinePillToggle'
import { BayesianResultsSummary, Experiment } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  getMetricResult,
  getVariantIdentities,
} from 'components/experiments/results/derive'
import {
  ConversionStackMode,
  REST_SUFFIX,
  buildConversionRateChartData,
  buildConversionStackChartData,
} from 'components/experiments/results/deriveConversionRate'

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
  const [mode, setMode] = useState<ConversionStackMode>('cumulative')
  const metric = getPrimaryMetric(experiment)
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )
  const chart = useMemo(
    () =>
      metric && results
        ? buildConversionStackChartData(
            results,
            metric.metric,
            identities,
            mode,
          )
        : null,
    [metric, results, identities, mode],
  )
  // Running counts and rates, for the cumulative tooltip ("x of y (z%)").
  const rateChart = useMemo(
    () =>
      metric && results
        ? buildConversionRateChartData(results, metric.metric, identities)
        : null,
    [metric, results, identities],
  )

  const formatTooltipValue = useCallback(
    (value: number, seriesKey: string, label: string) => {
      if (mode === 'daily') return value.toLocaleString()
      if (seriesKey.endsWith(REST_SUFFIX)) {
        // The faded segment is labelled "exposures", so report the full bar
        // total rather than the plotted remainder (exposures − conversions).
        const variantKey = seriesKey.slice(0, -REST_SUFFIX.length)
        const counts = rateChart?.countsByDay[label]?.[variantKey]
        return (counts?.exposed ?? value).toLocaleString()
      }
      const counts = rateChart?.countsByDay[label]?.[seriesKey]
      if (!counts) return value.toLocaleString()
      const rate = rateChart?.points.find((p) => p.day === label)?.[seriesKey]
      return `${counts.converted.toLocaleString()} of ${counts.exposed.toLocaleString()}${
        typeof rate === 'number' ? ` (${rate}%)` : ''
      }`
    },
    [mode, rateChart],
  )

  // Hidden entirely when no rate can be charted: value metrics, and
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
      className='experiment-results__conversion-rate-card'
      title='Conversion rate over time'
    >
      {hasConversions ? (
        <>
          {/* mt-n2 halves the card's 16px child gap after the title. */}
          <div className='d-flex mt-n2'>
            <InlinePillToggle<ConversionStackMode>
              size='small'
              options={[
                { label: 'Cumulative', value: 'cumulative' },
                { label: 'Daily', value: 'daily' },
              ]}
              value={mode}
              onChange={setMode}
            />
          </div>
          <BarChart
            data={chart.points}
            height={260}
            series={chart.series}
            showLegend
            tooltip={{ formatValue: formatTooltipValue }}
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
