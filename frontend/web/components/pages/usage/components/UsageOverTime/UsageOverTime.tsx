import { FC, useMemo } from 'react'
import Format from 'common/utils/format'
import { Res } from 'common/types/responses'
import { colorSurfaceAction, colorTextSecondary } from 'common/theme/tokens'
import EmptyState from 'components/EmptyState'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import BarChart from 'components/charts/BarChart'
import LineChart from 'components/charts/LineChart'
import {
  cumulativeTotals,
  dailyTotals,
  planLimitThreshold,
  withProjection,
  xAxisIntervalFor,
} from './utils'

type UsageOverTimeProps = {
  data: Res['organisationUsage'] | undefined
  limit: PlanLimit
  isBillingPeriod: boolean
  periodLabel: string
  /** Where usage is heading, and when the period it runs to ends. */
  projectedTotal?: number
  periodEndsAt?: string
}

const headingFor = (isBillingPeriod: boolean, limit: PlanLimit) => {
  if (!isBillingPeriod) return 'Daily usage'
  return limit ? 'Usage vs plan limit' : 'Cumulative usage'
}

const UsageOverTime: FC<UsageOverTimeProps> = ({
  data,
  isBillingPeriod,
  limit,
  periodEndsAt,
  periodLabel,
  projectedTotal,
}) => {
  const daily = useMemo(() => dailyTotals(data), [data])

  const cumulative = useMemo(() => cumulativeTotals(daily), [daily])

  const showsProjection = projectedTotal !== undefined && !!periodEndsAt
  const line = useMemo(
    () =>
      showsProjection
        ? withProjection(cumulative, projectedTotal, periodEndsAt)
        : cumulative,
    [cumulative, periodEndsAt, projectedTotal, showsProjection],
  )

  const xAxisInterval = xAxisIntervalFor(daily.length)

  const chart = isBillingPeriod ? (
    <LineChart
      data={line}
      series={showsProjection ? ['cumulative', 'projected'] : ['cumulative']}
      dashedSeries={['projected']}
      seriesLabels={{
        cumulative: 'API calls used',
        projected: 'Projected',
      }}
      colorMap={{
        cumulative: colorSurfaceAction,
        projected: colorTextSecondary,
      }}
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
        <strong>{headingFor(isBillingPeriod, limit)}</strong>
        <span className='fs-captionSmall text-secondary'>
          {Format.shortenNumber(data?.totals?.total ?? 0)} API calls ·{' '}
          {periodLabel}
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
