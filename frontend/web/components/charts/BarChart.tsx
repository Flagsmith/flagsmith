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
import { ChartDataPoint } from './types'

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
  /** Chart height in pixels. Default 400. */
  height?: number
  /**
   * Render series side by side instead of stacked. Required for non-additive
   * values (rates, percentages) where stacking would be meaningless.
   */
  grouped?: boolean
  /**
   * dataKey → stack id, for part-of-whole bars: series sharing a stack id
   * stack together, distinct ids sit side by side (e.g. converted/remainder
   * segments stacked per variant, variants grouped). Overrides `grouped`.
   */
  stackMap?: Record<string, string>
  /**
   * dataKey → fill opacity (0–1). Colours are CSS `var()` strings, so
   * transparency must come from SVG fill-opacity, not an alpha channel.
   */
  opacityMap?: Record<string, number>
  /** Left axis overrides, e.g. a `%` tick formatter. */
  yAxis?: {
    tickFormatter?: (value: number) => string
    domain?: [number, number]
  }
  /**
   * Per-entry tooltip value renderer, threaded to ChartTooltip. Skipped for
   * missing or non-numeric values, which render blank.
   */
  tooltipValueFormatter?: (
    value: number,
    seriesKey: string,
    label: string,
  ) => string
  /**
   * Hide the tooltip's total row — required when `tooltipValueFormatter`
   * renders a non-additive unit such as a percentage.
   */
  tooltipHideTotal?: boolean
}

type FadedSwatchLegendProps = {
  opacityMap: Record<string, number>
  seriesLabels?: Record<string, string>
  // Injected by recharts' <Legend content={...}>.
  payload?: { value?: string | number; color?: string }[]
}

const FadedSwatchLegend: FC<FadedSwatchLegendProps> = ({
  opacityMap,
  payload,
  seriesLabels,
}) => (
  <div className='d-flex justify-content-center flex-wrap gap-3'>
    {payload?.map((entry) => {
      const key = String(entry.value)
      return (
        <span className='d-flex align-items-center gap-1' key={key}>
          <span
            style={{
              backgroundColor: entry.color,
              display: 'inline-block',
              height: 10,
              opacity: opacityMap[key] ?? 1,
              width: 10,
            }}
          />
          <span style={{ color: entry.color, fontSize: 12 }}>
            {seriesLabels?.[key] ?? key}
          </span>
        </span>
      )
    })}
  </div>
)

const BarChart: FC<BarChartProps> = ({
  barSize,
  colorMap,
  data,
  grouped = false,
  height = 400,
  opacityMap,
  series,
  seriesLabels,
  showLegend = false,
  stackMap,
  tooltipHideTotal,
  tooltipValueFormatter,
  verticalGrid = true,
  xAxisInterval = 0,
  yAxis,
}) => {
  const defaultStackId = grouped ? undefined : 'series'
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
          domain={yAxis?.domain}
          tickFormatter={
            yAxis?.tickFormatter ??
            ((value) =>
              value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value)
          }
        />
        <Tooltip
          cursor={{ fill: 'transparent' }}
          content={
            <ChartTooltip
              hideTotal={tooltipHideTotal}
              seriesLabels={seriesLabels}
              valueFormatter={tooltipValueFormatter}
            />
          }
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) =>
              seriesLabels?.[String(value)] ?? String(value)
            }
            content={
              // The default legend swatch ignores fillOpacity, so faded
              // series need their own renderer to match the bars.
              opacityMap ? (
                <FadedSwatchLegend
                  opacityMap={opacityMap}
                  seriesLabels={seriesLabels}
                />
              ) : undefined
            }
          />
        )}
        {series.map((label, index) => (
          <Bar
            key={label}
            dataKey={label}
            stackId={stackMap ? stackMap[label] : defaultStackId}
            fill={colorMap[label]}
            fillOpacity={opacityMap?.[label]}
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
