import React, { FC } from 'react'
import {
  Cell,
  Legend,
  Pie,
  PieChart as RawPieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { colorTextSecondary } from 'common/theme/tokens'
import ChartTooltip from './ChartTooltip'

export type PieSlice = {
  name: string
  value: number
}

type PieChartProps = {
  data: PieSlice[]
  /** Per-slice colour, keyed by slice `name`. */
  colorMap: Record<string, string>
  /**
   * Chart height in pixels. Width is fluid — the chart fills its parent's
   * width via `<ResponsiveContainer>`. Default: 240. When `showLegend` is
   * true, remember to reserve vertical space for the legend too.
   */
  height?: number
  /** Inner radius in pixels. Set `> 0` for a donut. Default: 0 (solid pie). */
  innerRadius?: number
  /** Outer radius in pixels. Default: 80. */
  outerRadius?: number
  /** Gap between slices in degrees. Default: 2. */
  paddingAngle?: number
  /** Render recharts' built-in `<Legend />` below the chart. Default `false`. */
  showLegend?: boolean
  /** Show the hover tooltip. Default: true. */
  showTooltip?: boolean
  /**
   * Optional name → display name map for legend and tooltip entries. Useful
   * when slice names are opaque identifiers.
   */
  seriesLabels?: Record<string, string>
}

const PieChart: FC<PieChartProps> = ({
  colorMap,
  data,
  height = 240,
  innerRadius = 0,
  outerRadius = 80,
  paddingAngle = 2,
  seriesLabels,
  showLegend = false,
  showTooltip = true,
}) => {
  return (
    <ResponsiveContainer width='100%' height={height}>
      <RawPieChart>
        <Pie
          data={data}
          dataKey='value'
          nameKey='name'
          cx='50%'
          cy='50%'
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={paddingAngle}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={colorMap[entry.name] ?? colorTextSecondary}
            />
          ))}
        </Pie>
        {showTooltip && (
          <Tooltip
            content={<ChartTooltip seriesLabels={seriesLabels} hideTotal />}
          />
        )}
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) =>
              seriesLabels?.[String(value)] ?? String(value)
            }
          />
        )}
      </RawPieChart>
    </ResponsiveContainer>
  )
}

PieChart.displayName = 'PieChart'
export default PieChart
