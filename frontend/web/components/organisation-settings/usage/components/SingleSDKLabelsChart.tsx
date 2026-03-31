import React from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip as _Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts'
import moment from 'moment'
import { ChartDataPoint } from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import useChartTheme from 'common/hooks/useChartTheme'
import ChartTooltip from 'components/charts/ChartTooltip'

interface UsageChartProps {
  colours: string[]
  title: string
  data: ChartDataPoint[]
  userAgents?: string[]
  userAgentsColorMap: Map<string, string>
  metricKey: string
}

const UsageChart: React.FC<UsageChartProps> = ({
  colours,
  data,
  metricKey,
  title,
  userAgents = [],
  userAgentsColorMap,
}) => {
  const chartTheme = useChartTheme()
  return (
    <div className='border rounded p-3'>
      <h5>{title}</h5>
      <ResponsiveContainer height={400} width='100%'>
        <BarChart data={data}>
          <CartesianGrid stroke={chartTheme.gridStroke} vertical={false} />
          <_Tooltip
            cursor={{ fill: 'transparent' }}
            content={
              <ChartTooltip formatLabel={(v) => moment(v).format('D MMM')} />
            }
          />
          <XAxis
            dataKey='day'
            tickFormatter={(v) => moment(v).format('D MMM')}
            interval={data?.length > 31 ? 7 : 0}
            textAnchor='end'
            axisLine={{ stroke: chartTheme.axisStroke }}
            tick={{ dx: -4, fill: chartTheme.tickFill }}
            angle={-90}
            tickLine={false}
            allowDataOverflow={false}
          />
          <YAxis
            allowDataOverflow={false}
            tickLine={false}
            axisLine={{ stroke: chartTheme.axisStroke }}
            tick={{ fill: chartTheme.tickFill }}
          />
          <Legend wrapperStyle={{ paddingTop: '30px' }} />
          {userAgents?.map((userAgent, index) => (
            <Bar
              key={userAgent}
              dataKey={userAgent}
              stackId={metricKey}
              fill={
                userAgentsColorMap
                  ? userAgentsColorMap.get(userAgent)
                  : colours[index % colours.length]
              }
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default UsageChart
