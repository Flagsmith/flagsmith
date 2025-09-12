import Utils from 'common/utils/utils'
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
} from 'recharts'
import moment from 'moment'
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import { AggregateUsageDataItem } from 'common/types/responses'
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
            <CartesianGrid stroke='#EFF1F4' vertical={false} />
            <XAxis
              padding='gap'
              allowDataOverflow={false}
              dataKey='day'
              interval={chartData?.length > 31 ? 7 : 0}
              height={120}
              angle={-90}
              textAnchor='end'
              tickFormatter={(v) => moment(v).format('D MMM')}
              axisLine={{ stroke: '#EFF1F4' }}
              tick={{ dx: -4, fill: '#656D7B' }}
              tickLine={false}
            />
            <YAxis
              allowDataOverflow={false}
              tickLine={false}
              axisLine={{ stroke: '#EFF1F4' }}
              tick={{ fill: '#1A2634' }}
            />
            <_Tooltip
              cursor={{ fill: 'transparent' }}
              content={<RechartsTooltip />}
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
        const { dataKey, fill, payload } = el
        switch (dataKey) {
          case 'traits': {
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
                  Traits: {Utils.numberWithCommas(payload[dataKey])}
                </span>
              </Row>
            )
          }
          case 'flags': {
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
                  Flags: {Utils.numberWithCommas(payload[dataKey])}
                </span>
              </Row>
            )
          }
          case 'identities': {
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
                  Identities: {Utils.numberWithCommas(payload[dataKey])}
                </span>
              </Row>
            )
          }
          case 'environment_document': {
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
                  Environment Document:{' '}
                  {Utils.numberWithCommas(payload[dataKey])}
                </span>
              </Row>
            )
          }
          default: {
            return null
          }
        }
      })}
    </div>
  )
}

export default OrganisationUsage
