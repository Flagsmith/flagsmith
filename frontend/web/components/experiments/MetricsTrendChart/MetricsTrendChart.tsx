import { FC, useState } from 'react'
import LineChart from 'components/charts/LineChart'
import { ChartDataPoint } from 'components/charts/types'
import { colorChart5, colorTextSuccess } from 'common/theme/tokens'
import './MetricsTrendChart.scss'

export type MetricTrendPoint = {
  day: string
  control: number
  variant: number
}

export type MetricTrend = {
  metricName: string
  data: MetricTrendPoint[]
}

type MetricsTrendChartProps = {
  trends: MetricTrend[]
}

const SERIES = ['control', 'variant']
const COLOR_MAP: Record<string, string> = {
  control: colorTextSuccess,
  variant: colorChart5,
}
const SERIES_LABELS: Record<string, string> = {
  control: 'Control',
  variant: 'Variant B',
}

const MetricsTrendChart: FC<MetricsTrendChartProps> = ({ trends }) => {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const selected = trends[selectedIndex]

  if (!selected) return null

  const chartData: ChartDataPoint[] = selected.data.map((point) => ({
    control: point.control,
    day: point.day,
    variant: point.variant,
  }))

  return (
    <div className='metrics-trend-chart'>
      <div className='metrics-trend-chart__controls'>
        <span className='metrics-trend-chart__label'>Metric</span>
        <select
          className='metrics-trend-chart__select'
          value={selectedIndex}
          onChange={(e) => setSelectedIndex(Number(e.target.value))}
        >
          {trends.map((trend, i) => (
            <option key={trend.metricName} value={i}>
              {trend.metricName}
            </option>
          ))}
        </select>
      </div>
      <LineChart
        data={chartData}
        series={SERIES}
        colorMap={COLOR_MAP}
        seriesLabels={SERIES_LABELS}
        showLegend
        xAxisInterval={1}
      />
    </div>
  )
}

export default MetricsTrendChart
