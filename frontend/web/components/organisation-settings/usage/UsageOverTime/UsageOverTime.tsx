import { FC, useMemo } from 'react'
import { Res } from 'common/types/responses'
import { colorSurfaceAction } from 'common/theme/tokens'
import EmptyState from 'components/EmptyState'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import BarChart from 'components/charts/BarChart'
import LineChart from 'components/charts/LineChart'
import {
  cumulativeTotals,
  dailyTotals,
  planLimitThreshold,
  xAxisIntervalFor,
} from './utils'

type UsageOverTimeProps = {
  data: Res['organisationUsage'] | undefined
  limit: PlanLimit
  isBillingPeriod: boolean
}

/**
 * A rolling window's total falls as old days drop out of it, so only a billing
 * period is drawn cumulatively against the limit. Rolling windows get daily
 * volume instead.
 */
const UsageOverTime: FC<UsageOverTimeProps> = ({
  data,
  isBillingPeriod,
  limit,
}) => {
  const daily = useMemo(() => dailyTotals(data), [data])

  const cumulative = useMemo(() => cumulativeTotals(daily), [daily])

  const xAxisInterval = xAxisIntervalFor(daily.length)

  const chart = isBillingPeriod ? (
    <LineChart
      data={cumulative}
      series={['cumulative']}
      seriesLabels={{ cumulative: 'API calls used' }}
      colorMap={{ cumulative: colorSurfaceAction }}
      xAxisInterval={xAxisInterval}
      verticalGrid={false}
      height={320}
      referenceLine={planLimitThreshold(limit)}
    />
  ) : (
    <BarChart
      data={daily}
      series={['total']}
      seriesLabels={{ total: 'API calls' }}
      colorMap={{ total: colorSurfaceAction }}
      xAxisInterval={xAxisInterval}
      verticalGrid={false}
      barSize={14}
    />
  )

  return (
    <div className='p-4 border border-default rounded-lg bg-surface-default'>
      <div className='d-flex align-items-baseline justify-content-between gap-3 mb-3'>
        <strong>
          {isBillingPeriod ? 'Usage vs plan limit' : 'Daily usage'}
        </strong>
        <span className='fs-captionSmall text-secondary'>
          {isBillingPeriod
            ? 'Cumulative · this billing period'
            : 'Per day · rolling window'}
        </span>
      </div>
      {daily.length ? (
        chart
      ) : (
        <EmptyState
          title='No usage recorded'
          description='No usage data available for the selected period and project.'
          icon='bar-chart'
        />
      )}
    </div>
  )
}

export default UsageOverTime
