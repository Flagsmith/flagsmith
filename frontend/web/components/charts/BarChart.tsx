import React, { FC } from 'react'
import {
  Bar,
  BarChart as RawBarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { colorTextSecondary } from 'common/theme/tokens'
import ChartTooltip from './ChartTooltip'

export type ChartDataPoint = {
  day: string
} & Record<string, number>

type BarChartProps = {
  data: ChartDataPoint[]
  series: string[]
  colorMap: Record<string, string>
  xAxisInterval?: number
  /**
   * Render recharts' built-in `<Legend />` below the chart. Default `false` —
   * most consumers already expose a coloured filter UI (tags / MultiSelect)
   * that serves the same purpose, so a second legend is redundant and can
   * display raw dataKeys (e.g. numeric env IDs) that are meaningless to users.
   */
  showLegend?: boolean
  /**
   * Optional dataKey → display name map, threaded through to the tooltip (and
   * the legend when enabled). Use this when dataKeys are opaque identifiers
   * (e.g. numeric env ids) that need a human-readable label on display.
   */
  seriesLabels?: Record<string, string>
  /** Fixed bar width in pixels. Default: recharts auto-sizes by available space. */
  barSize?: number
  /** Render vertical grid lines (one per x tick). Default `true`. */
  verticalGrid?: boolean
}

const BarChart: FC<BarChartProps> = ({
  barSize,
  colorMap,
  data,
  series,
  seriesLabels,
  showLegend = false,
  verticalGrid = true,
  xAxisInterval = 0,
}) => {
  return (
    <ResponsiveContainer height={400} width='100%'>
      <RawBarChart data={data}>
        <CartesianGrid
          strokeDasharray='3 5'
          strokeOpacity={0.4}
          vertical={verticalGrid}
        />
        <XAxis
          dataKey='day'
          padding='gap'
          interval={xAxisInterval}
          height={80}
          angle={-90}
          textAnchor='end'
          tick={{ dx: -4, fill: colorTextSecondary, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: colorTextSecondary }}
        />
        <YAxis
          tick={{ fill: colorTextSecondary, fontSize: 11 }}
          axisLine={{ stroke: colorTextSecondary }}
          tickFormatter={(value) =>
            value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value
          }
        />
        <Tooltip
          cursor={{ fill: 'transparent' }}
          content={<ChartTooltip seriesLabels={seriesLabels} />}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) =>
              seriesLabels?.[String(value)] ?? String(value)
            }
          />
        )}
        {series.map((label, index) => (
          <Bar
            key={label}
            dataKey={label}
            stackId='series'
            fill={colorMap[label]}
            barSize={barSize}
            animationBegin={index * 80}
            animationDuration={600}
            animationEasing='ease-out'
          />
        ))}
      </RawBarChart>
    </ResponsiveContainer>
  )
}

BarChart.displayName = 'BarChart'
export default BarChart
