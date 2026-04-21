import React, { FC, useMemo, useState } from 'react'
import SearchableSelect, {
  OptionType,
} from 'components/base/select/SearchableSelect'
import LineChart from 'components/charts/LineChart'
import { ChartDataPoint } from 'components/charts/types'
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

const MetricsTrendChart: FC<MetricsTrendChartProps> = ({ trends }) => {
  const [selectedMetric, setSelectedMetric] = useState<string>(
    trends[0]?.metricName ?? '',
  )

  const options = useMemo<OptionType[]>(
    () => trends.map((t) => ({ label: t.metricName, value: t.metricName })),
    [trends],
  )

  const selected = trends.find((t) => t.metricName === selectedMetric)

  const data: ChartDataPoint[] = useMemo(
    () =>
      (selected?.data ?? []).map((p) => ({
        control: p.control,
        day: String(p.day),
        treatment: p.treatment,
      })),
    [selected],
  )

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
        data={data}
        series={SERIES}
        seriesLabels={SERIES_LABELS}
        colorMap={COLOR_MAP}
        showLegend
      />
    </div>
  )
}

MetricsTrendChart.displayName = 'MetricsTrendChart'
export default MetricsTrendChart
