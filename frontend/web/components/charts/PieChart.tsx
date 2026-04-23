import React, { FC } from 'react'
import { Cell, Legend, Pie, PieChart as RawPieChart, Tooltip } from 'recharts'

export type PieSlice = {
  name: string
  value: number
}

type PieChartProps = {
  data: PieSlice[]
  /** Per-slice colour, keyed by slice `name`. */
  colorMap: Record<string, string>
  /** Chart dimensions in pixels. Default: 200. */
  size?: number
  /** Inner radius in pixels. Set `> 0` for a donut. Default: 0 (solid pie). */
  innerRadius?: number
  /** Outer radius in pixels. Default: derived from `size` with a small margin. */
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
  innerRadius = 0,
  outerRadius,
  paddingAngle = 2,
  seriesLabels,
  showLegend = false,
  showTooltip = true,
  size = 200,
}) => {
  const resolvedOuter = outerRadius ?? Math.floor(size / 2) - 10

  return (
    <RawPieChart width={size} height={size}>
      <Pie
        data={data}
        dataKey='value'
        nameKey='name'
        cx='50%'
        cy='50%'
        innerRadius={innerRadius}
        outerRadius={resolvedOuter}
        paddingAngle={paddingAngle}
      >
        {data.map((entry) => (
          <Cell key={entry.name} fill={colorMap[entry.name]} />
        ))}
      </Pie>
      {showTooltip && (
        <Tooltip
          formatter={(value: number, name: string) => [
            value.toLocaleString(),
            seriesLabels?.[name] ?? name,
          ]}
        />
      )}
      {showLegend && (
        <Legend
          wrapperStyle={{ paddingTop: 16 }}
          formatter={(value) => seriesLabels?.[String(value)] ?? String(value)}
        />
      )}
    </RawPieChart>
  )
}

PieChart.displayName = 'PieChart'
export default PieChart
