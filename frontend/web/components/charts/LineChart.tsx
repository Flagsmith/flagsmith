import React, { FC } from 'react'
import { AxisDomain } from 'recharts/types/util/types'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart as RawLineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { colorTextSecondary } from 'common/theme/tokens'
import ChartTooltip from './ChartTooltip'
import { ChartDataPoint } from './types'

type LineChartProps = {
  data: ChartDataPoint[]
  series: string[]
  colorMap: Record<string, string>
  height?: number
  xAxisInterval?: number
  showLegend?: boolean
  seriesLabels?: Record<string, string>
  verticalGrid?: boolean
  /**
   * A horizontal threshold drawn across the chart, for a limit or a target.
   * The y-axis grows to include it, so the line is always in view.
   */
  referenceLine?: Threshold
}

type Threshold = { value: number; label?: string; colour: string }

// Room above the highest of the data and the threshold, so the topmost label
// is not clipped by the edge of the plot.
const axisDomainFor = (referenceLine?: Threshold): AxisDomain | undefined =>
  referenceLine
    ? [
        0,
        (max: number) => Math.round(Math.max(max, referenceLine.value) * 1.08),
      ]
    : undefined

const thresholdLabelFor = (referenceLine?: Threshold) =>
  referenceLine?.label
    ? {
        fill: referenceLine.colour,
        fontSize: 11,
        position: 'insideTopRight' as const,
        value: referenceLine.label,
      }
    : undefined

const LineChart: FC<LineChartProps> = ({
  colorMap,
  data,
  height = 400,
  referenceLine,
  series,
  seriesLabels,
  showLegend = false,
  verticalGrid = true,
  xAxisInterval = 0,
}) => {
  return (
    <ResponsiveContainer height={height} width='100%'>
      <RawLineChart data={data}>
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
          domain={axisDomainFor(referenceLine)}
          tickFormatter={(value) =>
            value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value
          }
        />
        <Tooltip
          cursor={{ stroke: colorTextSecondary, strokeDasharray: '3 3' }}
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
        {referenceLine && (
          <ReferenceLine
            y={referenceLine.value}
            stroke={referenceLine.colour}
            strokeWidth={2}
            label={thresholdLabelFor(referenceLine)}
          />
        )}
        {series.map((label, index) => (
          <Line
            key={label}
            type='monotone'
            dataKey={label}
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
