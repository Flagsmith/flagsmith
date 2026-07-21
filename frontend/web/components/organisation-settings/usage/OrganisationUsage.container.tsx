import React, { FC, useMemo } from 'react'
import moment from 'moment'
import { AggregateUsageDataItem } from 'common/types/responses'
import EmptyState from 'components/EmptyState'
import BarChart, { ChartDataPoint } from 'components/charts/BarChart'
import UsageAPIDefinitions from './components/UsageAPIDefinitions'

type OrganisationUsageProps = {
  chartData: AggregateUsageDataItem[]
  isError: boolean
  selection: string[]
  colours: string[]
}

// Stable mapping between the user-facing selection label and the API field
// (and therefore the chart's dataKey).
const METRICS = [
  { dataKey: 'flags', label: 'Flags' },
  { dataKey: 'identities', label: 'Identities' },
  { dataKey: 'environment_document', label: 'Environment Document' },
  { dataKey: 'traits', label: 'Traits' },
] as const

type MetricDataKey = (typeof METRICS)[number]['dataKey']

const OrganisationUsage: FC<OrganisationUsageProps> = ({
  chartData,
  colours,
  isError,
  selection,
}) => {
  const formattedData: ChartDataPoint[] = useMemo(
    () =>
      chartData?.map((d) => ({
        day: moment(d.day).format('D MMM'),
        environment_document: d.environment_document ?? 0,
        flags: d.flags ?? 0,
        identities: d.identities ?? 0,
        traits: d.traits ?? 0,
      })) ?? [],
    [chartData],
  )

  const series = useMemo(
    () =>
      METRICS.filter((m) => selection.includes(m.label)).map((m) => m.dataKey),
    [selection],
  )

  // dataKey → its colour at the metric's index in METRICS, so colours stay
  // stable per metric regardless of which selections are active. Typed as
  // `Record<MetricDataKey, …>` so adding a new entry to METRICS forces this
  // (and seriesLabels below) to be updated — TS will fail compilation if any
  // dataKey is missing.
  const colorMap = useMemo<Record<MetricDataKey, string>>(
    () => ({
      environment_document: colours[2],
      flags: colours[0],
      identities: colours[1],
      traits: colours[3],
    }),
    [colours],
  )

  // dataKey → display name (so the tooltip says "Environment Document"
  // instead of "environment_document").
  const seriesLabels: Record<MetricDataKey, string> = {
    environment_document: 'Environment Document',
    flags: 'Flags',
    identities: 'Identities',
    traits: 'Traits',
  }

  if (!chartData && !isError) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <>
      {isError || chartData?.length === 0 ? (
        <EmptyState
          title={isError ? 'No billing periods' : 'No usage recorded'}
          description={
            isError
              ? 'Your organisation does not have recurrent billing periods.'
              : 'No usage data available for the selected period and project.'
          }
          icon='bar-chart'
        />
      ) : (
        <BarChart
          data={formattedData}
          series={series}
          colorMap={colorMap}
          seriesLabels={seriesLabels}
          xAxisInterval={chartData?.length > 31 ? 7 : 0}
          barSize={14}
          verticalGrid={false}
        />
      )}
      <UsageAPIDefinitions />
    </>
  )
}

export default OrganisationUsage
