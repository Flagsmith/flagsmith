import React, { FC } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart as RawLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { colorTextSecondary } from 'common/theme/tokens'

export type LineChartDataPoint = {
  day: string | number
} & Record<string, number>

type LineChartProps = {
  data: LineChartDataPoint[]
  series: string[]
  colorMap: Record<string, string>
  /**
   * Optional dataKey → display name map, used for the legend and tooltip when
   * dataKeys differ from the label users should see.
   */
  seriesLabels?: Record<string, string>
  showLegend?: boolean
  xAxisLabel?: string
  yAxisFormatter?: (value: number) => string
  tooltipValueFormatter?: (value: number) => string
  tooltipLabelFormatter?: (label: string | number) => string
  height?: number
}

const LineChart: FC<LineChartProps> = ({
  colorMap,
  data,
  height = 320,
  series,
  seriesLabels,
  showLegend = true,
  tooltipLabelFormatter,
  tooltipValueFormatter,
  xAxisLabel,
  yAxisFormatter,
}) => {
  return (
    <ResponsiveContainer height={height} width='100%'>
      <RawLineChart
        data={data}
        margin={{ bottom: 8, left: 8, right: 16, top: 16 }}
      >
        <CartesianGrid strokeDasharray='3 5' strokeOpacity={0.4} />
        <XAxis
          dataKey='day'
          tick={{ fill: colorTextSecondary, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: colorTextSecondary }}
          label={
            xAxisLabel
              ? {
                  fill: colorTextSecondary,
                  fontSize: 11,
                  offset: -4,
                  position: 'insideBottom',
                  value: xAxisLabel,
                }
              : undefined
          }
        />
        <YAxis
          tick={{ fill: colorTextSecondary, fontSize: 11 }}
          axisLine={{ stroke: colorTextSecondary }}
          tickFormatter={yAxisFormatter}
          width={60}
        />
        <Tooltip
          formatter={
            tooltipValueFormatter
              ? (value: number) => tooltipValueFormatter(value)
              : undefined
          }
          labelFormatter={tooltipLabelFormatter}
          contentStyle={{
            background: 'var(--color-surface-default)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
          }}
        />
        {showLegend && (
          <Legend
            verticalAlign='top'
            height={32}
            iconType='plainline'
            wrapperStyle={{ fontSize: 12 }}
            formatter={(value) =>
              seriesLabels?.[String(value)] ?? String(value)
            }
          />
        )}
        {series.map((label, index) => (
          <Line
            key={label}
            type='monotone'
            dataKey={label}
            name={seriesLabels?.[label] ?? label}
            stroke={colorMap[label]}
            strokeWidth={2}
            dot={false}
            animationBegin={index * 80}
            animationDuration={600}
            animationEasing='ease-out'
          />
        ))}
      </RawLineChart>
    </ResponsiveContainer>
  )
}

LineChart.displayName = 'LineChart'
export default LineChart
