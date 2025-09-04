import React, { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Button from 'components/base/forms/Button'
import { FlagAnalyticsData } from 'components/feature-page/FeatureNavTab/FeatureAnalytics/FeatureAnalytics.container'

interface FeatureAnalyticsChartProps {
  usageData?: FlagAnalyticsData[]
}

const FeatureAnalyticsChart: React.FC<FeatureAnalyticsChartProps> = ({
  usageData,
}) => {
  const aggregatedData = useMemo(() => {
    return usageData?.length
      ? Object.values(
          usageData.reduce(
            (acc: Record<string, { day: string; count: number }>, item) => {
              const day = item.day
              if (!acc[day]) {
                acc[day] = {
                  count: 0,
                  day: day,
                }
              }
              acc[day].count += item.count || 0
              return acc
            },
            {},
          ),
        )
      : []
  }, [usageData])

  return aggregatedData?.length ? (
    <ResponsiveContainer height={400} width='100%' className='mt-4'>
      <BarChart data={aggregatedData}>
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
      There has been no activity for this flag within the past month. Find out
      about Flag Analytics{' '}
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
  )
}

FeatureAnalyticsChart.displayName = 'FeatureAnalyticsChart'

export default React.memo(FeatureAnalyticsChart)
