import { FC, ReactNode } from 'react'
import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import EmptyState from 'components/EmptyState'
import UsageMeter from './components/UsageMeter'
import UsageOverTime from './components/UsageOverTime'

export type UsageDashboardProps = {
  data: Res['organisationUsage'] | undefined
  total: number
  limit: PlanLimit
  /**
   * Whether the selected period accumulates towards the limit. False for the
   * rolling windows, and for any plan without a billing term.
   */
  hasBillingPeriod: boolean
  isError?: boolean
  isLoading?: boolean
  filters?: ReactNode
}

const UsageDashboard: FC<UsageDashboardProps> = ({
  data,
  filters,
  hasBillingPeriod,
  isError,
  isLoading,
  limit,
  total,
}) => {
  // Loading and failure replace the figures rather than the whole page, so the
  // heading and the filters stay put. Without this the meter reads 0% in both,
  // which is indistinguishable from an organisation that made no calls.
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
      />
    )
  } else {
    content = (
      <>
        <UsageMeter total={total} limit={limit} />

        {/* Tile row waits for #8188 and #8258: alone it repeated the meter. */}

        <UsageOverTime
          data={data}
          limit={limit}
          isBillingPeriod={hasBillingPeriod}
        />
      </>
    )
  }

  return (
    <div className='px-3 px-md-4 py-4'>
      <Row space className='mb-4 align-items-end'>
        <h4 className='mb-0'>Usage</h4>
        {filters}
      </Row>

      {content}
    </div>
  )
}

export default UsageDashboard
