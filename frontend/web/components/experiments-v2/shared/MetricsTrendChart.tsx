import React, { FC, useMemo, useState } from 'react'
import SearchableSelect, {
  OptionType,
} from 'components/base/select/SearchableSelect'
import LineChart from 'components/charts/LineChart'
import { MetricTrend } from 'components/experiments-v2/types'
import './MetricsTrendChart.scss'

type MetricsTrendChartProps = {
  trends: MetricTrend[]
}

const SERIES = ['control', 'treatment']
const SERIES_LABELS: Record<string, string> = {
  control: 'Control',
  treatment: 'Treatment B',
}
const COLOR_MAP: Record<string, string> = {
  control: 'var(--green-500)',
  treatment: 'var(--purple-500)',
}

const formatValue = (unit: MetricTrend['unit'], value: number): string => {
  if (unit === '$') return `$${value.toFixed(2)}`
  if (unit === '%') return `${value.toFixed(1)}%`
  return `${value.toFixed(2)}s`
}

const formatAxis = (unit: MetricTrend['unit'], value: number): string => {
  if (unit === '$') return `$${value.toFixed(0)}`
  return `${value.toFixed(1)}${unit}`
}

const MetricsTrendChart: FC<MetricsTrendChartProps> = ({ trends }) => {
  const [selectedMetric, setSelectedMetric] = useState<string>(
    trends[0]?.metricName ?? '',
  )

  const options = useMemo<OptionType[]>(
    () => trends.map((t) => ({ label: t.metricName, value: t.metricName })),
    [trends],
  )

  const selected = trends.find((t) => t.metricName === selectedMetric)

  if (!selected) {
    return null
  }

  return (
    <div className='metrics-trend-chart'>
      <div className='metrics-trend-chart__controls'>
        <label className='metrics-trend-chart__label'>Metric</label>
        <div className='metrics-trend-chart__select'>
          <SearchableSelect
            value={selectedMetric}
            onChange={(opt: OptionType) => setSelectedMetric(String(opt.value))}
            options={options}
            placeholder='Select a metric...'
          />
        </div>
      </div>

      <LineChart
        data={selected.data}
        series={SERIES}
        seriesLabels={SERIES_LABELS}
        colorMap={COLOR_MAP}
        xAxisLabel='Day'
        yAxisFormatter={(value) => formatAxis(selected.unit, value)}
        tooltipValueFormatter={(value) => formatValue(selected.unit, value)}
        tooltipLabelFormatter={(label) => `Day ${label}`}
      />
    </div>
  )
}

MetricsTrendChart.displayName = 'MetricsTrendChart'
export default MetricsTrendChart
