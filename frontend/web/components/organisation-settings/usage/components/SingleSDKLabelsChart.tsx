import React, { FC } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip as _Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  TooltipProps,
  Legend,
} from 'recharts'
import moment from 'moment'
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import { ChartDataPoint } from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import Utils from 'common/utils/utils'

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
}) => (
  <div className='border rounded p-3'>
    <h5>{title}</h5>
    <ResponsiveContainer height={250} width='100%'>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray='3 3' />
        <_Tooltip
          cursor={{ fill: 'transparent' }}
          content={<RechartsTooltip />}
        />
        <XAxis
          dataKey='day'
          tickFormatter={(v) => moment(v).format('D MMM')}
          interval={7}
          axisLine={{ stroke: '#EFF1F4' }}
          tick={{ dx: -4, fill: '#656D7B' }}
          tickLine={false}
          allowDataOverflow={false}
        />
        <YAxis />
        <Legend />
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

const RechartsTooltip: FC<TooltipProps<ValueType, NameType>> = ({
  active,
  label,
  payload,
}) => {
  if (!active || !payload || payload.length === 0) {
    return null
  }

  return (
    <div className='recharts-tooltip py-2'>
      <div className='px-4 py-2 fs-small lh-sm fw-bold recharts-tooltip-header'>
        {moment(label).format('D MMM')}
      </div>
      <hr className='py-0 my-0 mb-3' />
      {payload.map((el: any) => {
        const { dataKey, fill, value } = el
        return (
          <Row key={dataKey} className='px-4 mb-3'>
            <span
              style={{
                backgroundColor: fill,
                borderRadius: 2,
                display: 'inline-block',
                height: 16,
                width: 16,
              }}
            />
            <span className='text-muted ml-2'>
              {dataKey}: {Utils.numberWithCommas(value)}
            </span>
          </Row>
        )
      })}
    </div>
  )
}

export default UsageChart
