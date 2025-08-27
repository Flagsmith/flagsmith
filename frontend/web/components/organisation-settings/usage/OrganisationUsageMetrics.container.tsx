import { Res } from 'common/types/responses'
import React, { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts'
import moment from 'moment'
import Utils from 'common/utils/utils'
import { Tooltip as _Tooltip } from 'recharts'

export interface OrganisationUsageMetricsProps {
  data: Res['organisationUsage']
  colours: string[]
}

const OrganisationUsageMetrics: React.FC<OrganisationUsageMetricsProps> = ({
  colours,
  data,
}) => {
  const flagsChartData = useMemo(() => {
    if (!data?.events_list) return []

    // Group by day, then by user_agent
    const grouped = data.events_list.reduce((acc, event) => {
      if (!event.flags) return acc // Skip if no flags data

      const date = event.day
      const userAgent = event.labels?.user_agent || 'Unknown'

      if (!acc[date]) acc[date] = { day: date }
      acc[date][userAgent] = (acc[date][userAgent] || 0) + event.flags

      return acc
    }, {} as Record<string, any>)

    return Object.values(grouped)
  }, [data?.events_list])

  // Unique user agents for legend/colors
  const userAgents = useMemo(() => {
    if (!data?.events_list) return []
    return [
      ...new Set(
        data.events_list.map((e) => e.labels?.user_agent || 'Unknown'),
      ),
    ]
  }, [data?.events_list])

  return (
    <div className='row'>
      <div className='col-12 col-lg-6 mb-4'>
        <div className='border rounded p-3'>
          <h5>Flags Analytics</h5>
          <ResponsiveContainer height={250} width='100%'>
            <BarChart data={flagsChartData}>
              <CartesianGrid strokeDasharray='3 3' />
              <_Tooltip
                cursor={{ fill: 'transparent' }}
                content={<RechartsTooltip />}
              />
              <XAxis
                dataKey='day'
                tickFormatter={(v) => moment(v).format('M/D')}
              />
              <YAxis />
              {userAgents.map((userAgent, index) => (
                <Bar
                  key={userAgent}
                  dataKey={userAgent}
                  stackId='flags'
                  fill={colours[index % colours.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className='col-12 col-lg-6 mb-4'>
        <div className='border rounded p-3'>
          <h5>Identities Analytics</h5>
          {/* Identities chart component */}
        </div>
      </div>

      <div className='col-12 col-lg-6 mb-4'>
        <div className='border rounded p-3'>
          <h5>Environment Documents Analytics</h5>
          {/* Environment Documents chart component */}
        </div>
      </div>

      <div className='col-12 col-lg-6 mb-4'>
        <div className='border rounded p-3'>
          <h5>Traits Analytics</h5>
          {/* Traits chart component */}
        </div>
      </div>
    </div>
  )
}

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

export default OrganisationUsageMetrics
