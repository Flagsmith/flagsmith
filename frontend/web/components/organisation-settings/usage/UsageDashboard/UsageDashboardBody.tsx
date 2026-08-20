import { FC } from 'react'
import { Res } from 'common/types/responses'
import EmptyState from 'components/EmptyState'
import UsageMeter from 'components/organisation-settings/usage/UsageMeter'
import UsageOverTime from 'components/organisation-settings/usage/UsageOverTime'

export type UsageDashboardBodyProps = {
  data: Res['organisationUsage'] | undefined
  total: number
  limit: number | null | undefined
  hasBillingPeriod: boolean
  isError?: boolean
  isLoading?: boolean
}

/**
 * Loading and failure are drawn instead of the figures. Without that the meter
 * reads 0% in both, which is indistinguishable from an org that made no calls.
 */
const UsageDashboardBody: FC<UsageDashboardBodyProps> = ({
  data,
  hasBillingPeriod,
  isError,
  isLoading,
  limit,
  total,
}) => {
  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (isError) {
    return (
      <EmptyState
        title='Usage could not be loaded'
        description='Something went wrong fetching usage for this period. Try again in a moment.'
        icon='bar-chart'
      />
    )
  }

  return (
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

export default UsageDashboardBody
