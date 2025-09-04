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
    <ResponsiveContainer height={400} width='100%'>
      <BarChart data={data}>
        <CartesianGrid stroke='#EFF1F4' vertical={false} />
        <_Tooltip
          cursor={{ fill: 'transparent' }}
          content={<RechartsTooltip />}
        />
        <XAxis
          dataKey='day'
          tickFormatter={(v) => moment(v).format('D MMM')}
          interval={data?.length > 31 ? 7 : 0}
          textAnchor='end'
          axisLine={{ stroke: '#EFF1F4' }}
          tick={{ dx: -4, fill: '#656D7B' }}
          angle={-90}
          tickLine={false}
          allowDataOverflow={false}
        />
        <YAxis
          allowDataOverflow={false}
          tickLine={false}
          axisLine={{ stroke: '#EFF1F4' }}
          tick={{ fill: '#1A2634' }}
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
