import React, { FC } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip as _Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import moment from 'moment'
import { AggregateUsageDataItem } from 'common/types/responses'
import useChartTheme from 'common/hooks/useChartTheme'
import ChartTooltip from 'components/charts/ChartTooltip'
import UsageAPIDefinitions from './components/UsageAPIDefinitions'

type OrganisationUsageProps = {
  chartData: AggregateUsageDataItem[]
  isError: boolean
  selection: string[]
  colours: string[]
}

const OrganisationUsage: FC<OrganisationUsageProps> = ({
  chartData,
  colours,
  isError,
  selection,
}) => {
  const chartTheme = useChartTheme()
  return chartData || isError ? (
    <>
      {isError || chartData?.length === 0 ? (
        <div className='py-4 fw-semibold text-center'>
          {isError
            ? 'Your organisation does not have recurrent billing periods'
            : 'No usage recorded.'}
        </div>
      ) : (
        <ResponsiveContainer height={400} width='100%'>
          <BarChart data={chartData} style={{ stroke: '#fff', strokeWidth: 1 }}>
            <CartesianGrid stroke={chartTheme.gridStroke} vertical={false} />
            <XAxis
              padding='gap'
              allowDataOverflow={false}
              dataKey='day'
              interval={chartData?.length > 31 ? 7 : 0}
              height={120}
              angle={-90}
              textAnchor='end'
              tickFormatter={(v) => moment(v).format('D MMM')}
              axisLine={{ stroke: chartTheme.axisStroke }}
              tick={{ dx: -4, fill: chartTheme.tickFill }}
              tickLine={false}
            />
            <YAxis
              allowDataOverflow={false}
              tickLine={false}
              axisLine={{ stroke: chartTheme.axisStroke }}
              tick={{ fill: chartTheme.tickFill }}
            />
            <_Tooltip
              cursor={{ fill: 'transparent' }}
              content={
                <ChartTooltip formatLabel={(v) => moment(v).format('D MMM')} />
              }
            />
            {selection.includes('Flags') && (
              <Bar dataKey='flags' barSize={14} stackId='a' fill={colours[0]} />
            )}
            {selection.includes('Identities') && (
              <Bar
                dataKey='identities'
                barSize={14}
                stackId='a'
                fill={colours[1]}
              />
            )}
            {selection.includes('Environment Document') && (
              <Bar
                name='Environment Document'
                dataKey='environment_document'
                stackId='a'
                fill={colours[2]}
                barSize={14}
              />
            )}
            {selection.includes('Traits') && (
              <Bar
                dataKey='traits'
                barSize={14}
                stackId='a'
                fill={colours[3]}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      )}
      <UsageAPIDefinitions />
    </>
  ) : (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default OrganisationUsage
