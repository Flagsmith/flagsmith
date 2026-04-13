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
  colorMap: Map<string, string>
  height?: number
  xAxisInterval?: number
  stacked?: boolean
}

const BarChart: FC<BarChartProps> = ({
  colorMap,
  data,
  height = 400,
  series,
  stacked = true,
  xAxisInterval = 0,
}) => {
  return (
    <ResponsiveContainer height={height} width='100%'>
      <RawBarChart data={data}>
        <CartesianGrid strokeDasharray='3 5' strokeOpacity={0.4} />
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
          tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
        />
        <Tooltip cursor={{ fill: 'transparent' }} content={<ChartTooltip />} />
        <Legend wrapperStyle={{ paddingTop: 16 }} />
        {series.map((label, index) => (
          <Bar
            key={label}
            dataKey={label}
            stackId={stacked ? 'series' : undefined}
            fill={colorMap.get(label)}
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
