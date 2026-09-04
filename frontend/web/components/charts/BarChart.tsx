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
import ColorSwatch from 'components/ColorSwatch'
import ChartTooltip from './ChartTooltip'
import { BarSeries, ChartDataPoint } from './types'

// Series with no stack id of their own share this one, so the default shape is
// a single stacked bar per x value.
const DEFAULT_STACK_ID = 'series'

type BarChartTooltipProps = {
  /**
   * Per-entry value renderer, e.g. `"120 of 1,450 (8.3%)"`. Skipped for
   * missing or non-numeric values, which render blank.
   */
  formatValue?: (value: number, seriesKey: string, label: string) => string
  /**
   * Hide the total row. A formatted value is usually not additive (a
   * percentage, an "x of y"), so `formatValue` hides the total by default;
   * pass `false` to keep it.
   */
  hideTotal?: boolean
}

type BarChartProps = {
  data: ChartDataPoint[]
  /**
   * One entry per bar series, in render order. `key` is the dataKey to read
   * from each `data` point; `stackId` and `opacity` shape how it draws.
   */
  series: BarSeries[]
  xAxisInterval?: number
  /**
   * Render a legend below the chart. Default `false` — most consumers already
   * expose a coloured filter UI (tags / MultiSelect) that serves the same
   * purpose, so a second legend is redundant.
   */
  showLegend?: boolean
  /** Fixed bar width in pixels. Default: recharts auto-sizes by available space. */
  barSize?: number
  /** Render vertical grid lines (one per x tick). Default `true`. */
  verticalGrid?: boolean
  /** Chart height in pixels. Default 400. */
  height?: number
  tooltip?: BarChartTooltipProps
}

type BarChartLegendProps = {
  series: BarSeries[]
  // Injected by recharts' <Legend content={...}>.
  payload?: { value?: string | number; color?: string }[]
}

// recharts' own legend swatch ignores fillOpacity, so a chart with faded
// series needs this to keep the key and the bars looking the same.
const FadedSwatchLegend: FC<BarChartLegendProps> = ({ payload, series }) => (
  <div className='d-flex justify-content-center flex-wrap gap-3'>
    {payload?.map((entry) => {
      const key = String(entry.value)
      const bar = series.find((s) => s.key === key)
      const colour = bar?.colour ?? entry.color ?? ''
      return (
        <span className='d-flex align-items-center gap-1' key={key}>
          <ColorSwatch color={colour} opacity={bar?.opacity} size='sm' />
          <span className='fs-captionSmall' style={{ color: colour }}>
            {bar?.label ?? key}
          </span>
        </span>
      )
    })}
  </div>
)

const BarChart: FC<BarChartProps> = ({
  barSize,
  data,
  height = 400,
  series,
  showLegend = false,
  tooltip,
  verticalGrid = true,
  xAxisInterval = 0,
}) => {
  const labels = series.reduce<Record<string, string>>((acc, s) => {
    acc[s.key] = s.label
    return acc
  }, {})
  const hasFadedSeries = series.some((s) => s.opacity !== undefined)
  return (
    <ResponsiveContainer height={height} width='100%'>
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
          content={
            <ChartTooltip
              hideTotal={tooltip?.hideTotal ?? !!tooltip?.formatValue}
              seriesLabels={labels}
              valueFormatter={tooltip?.formatValue}
            />
          }
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) => labels[String(value)] ?? String(value)}
            content={
              hasFadedSeries ? <FadedSwatchLegend series={series} /> : undefined
            }
          />
        )}
        {series.map((s, index) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            stackId={s.stackId ?? DEFAULT_STACK_ID}
            fill={s.colour}
            fillOpacity={s.opacity}
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
