import { FC, ReactNode } from 'react'
import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import EmptyState from 'components/EmptyState'
import OverLimitBanner, {
  OverLimitBannerProps,
} from './components/OverLimitBanner'
import SectionHeading from './components/SectionHeading'
import UsageMeter from './components/UsageMeter'
import UsageOverTime from './components/UsageOverTime'

export type UsageDashboardProps = {
  data: Res['organisationUsage'] | undefined
  total: number
  limit: PlanLimit
  planCopy: { title: string; hint: string }
  periodLabel: string
  meterNote?: ReactNode
  showPlanCeiling?: boolean
  hasBillingPeriod: boolean
  isError?: boolean
  isLoading?: boolean
  isExploring?: boolean
  onRetry?: () => void
  filters?: ReactNode
  breakdown?: ReactNode
  /** Set when the organisation has used more than its plan allows. */
  overLimit?: OverLimitBannerProps
}

const UsageDashboard: FC<UsageDashboardProps> = ({
  breakdown,
  data,
  filters,
  hasBillingPeriod,
  isError,
  isExploring,
  isLoading,
  limit,
  meterNote,
  onRetry,
  overLimit,
  periodLabel,
  planCopy,
  showPlanCeiling,
  total,
}) => {
  let content

  if (isLoading) {
    content = (
      <div className='text-center'>
        <Loader />
      </div>
    )
  } else if (isError) {
    content = (
      <EmptyState
        title='Usage could not be loaded'
        description='Something went wrong fetching usage for this period. Try again in a moment.'
        icon='bar-chart'
        action={
          onRetry && (
            <Button onClick={onRetry} theme='secondary'>
              Try again
            </Button>
          )
        }
      />
    )
  } else {
    content = (
      <>
        {overLimit && <OverLimitBanner {...overLimit} />}

        <SectionHeading title={planCopy.title} hint={planCopy.hint} />

        <UsageMeter total={total} limit={limit} note={meterNote} />

        <SectionHeading
          title='Explore usage'
          hint='Narrow the chart and the breakdown by period or project.'
          action={filters}
        />

        {isExploring ? (
          <div className='text-center py-5'>
            <Loader />
          </div>
        ) : (
          <>
            <UsageOverTime
              data={data}
              limit={showPlanCeiling ? limit : undefined}
              isBillingPeriod={hasBillingPeriod}
              periodLabel={periodLabel}
            />

            {breakdown}
          </>
        )}
      </>
    )
  }

  return (
    <div className='px-3 px-md-4 py-4'>
      <h4 className='mb-4'>Usage</h4>
      {content}
    </div>
  )
}

export default UsageDashboard
