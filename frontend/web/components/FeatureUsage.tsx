import React, { FC } from 'react'
import { useGetFeatureUsageQuery } from 'common/services/useFeatureUsage'
import InfoMessage from './InfoMessage'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts'
import Button from './base/forms/Button'

type FeatureUsageType = {
  featureId: number
  projectId: number
  environmentId: number
}

const FeatureUsage: FC<FeatureUsageType> = ({
  environmentId,
  featureId,
  projectId,
}) => {
  const { data: usageData } = useGetFeatureUsageQuery({
    environmentId,
    featureId,
    period: 30,
    projectId,
  })
  return (
    <>
      <FormGroup className='mb-4'>
        {!!usageData && <h5 className='mb-2'>Flag events for last 30 days</h5>}
        {!usageData && (
          <div className='text-center'>
            <Loader />
          </div>
        )}

        {usageData?.length ? (
          <ResponsiveContainer height={400} width='100%' className='mt-4'>
            <BarChart data={usageData}>
              <CartesianGrid strokeDasharray='3 5' strokeOpacity={0.4} />
              <XAxis
                padding='gap'
                interval={0}
                height={100}
                angle={-90}
                textAnchor='end'
                allowDataOverflow={false}
                dataKey='day'
                tick={{ dx: -4, fill: '#656D7B' }}
                tickLine={false}
                axisLine={{ stroke: '#656D7B' }}
              />
              <YAxis
                allowDataOverflow={false}
                tick={{ fill: '#656D7B' }}
                axisLine={{ stroke: '#656D7B' }}
              />
              <RechartsTooltip cursor={{ fill: 'transparent' }} />
              <Bar
                dataKey={'count'}
                stackId='a'
                fill='rgba(149, 108, 255,0.48)'
                barSize={14}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className='modal-caption fs-small lh-sm'>
            There has been no activity for this flag within the past month. Find
            out about Flag Analytics{' '}
            <Button
              theme='text'
              target='_blank'
              href='https://docs.flagsmith.com/advanced-use/flag-analytics'
              className='fw-normal'
            >
              here
            </Button>
            .
          </div>
        )}
      </FormGroup>
      <InfoMessage>
        The Flag Analytics data will be visible in the Dashboard between 30
        minutes and 1 hour after it has been collected.{' '}
        <a
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
          rel='noreferrer'
        >
          View docs
        </a>
      </InfoMessage>
    </>
  )
}

export default FeatureUsage
