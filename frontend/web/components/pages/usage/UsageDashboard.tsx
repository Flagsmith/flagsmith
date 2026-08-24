import { FC, ReactNode } from 'react'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import EmptyState from 'components/EmptyState'
import UsageBreakdown from './components/UsageBreakdown'
import UsageMeter from './components/UsageMeter'
import UsageOverTime from './components/UsageOverTime'

export type UsageDashboardProps = {
  data: Res['organisationUsage'] | undefined
  total: number
  limit: PlanLimit
  hasBillingPeriod: boolean
  isError?: boolean
  isLoading?: boolean
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  projectId: number | undefined
  filters?: ReactNode
}

const UsageDashboard: FC<UsageDashboardProps> = ({
  billingPeriod,
  data,
  filters,
  hasBillingPeriod,
  isError,
  isLoading,
  limit,
  organisationId,
  projectId,
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
      />
    )
  } else {
    content = (
      <>
        <UsageMeter total={total} limit={limit} />

        <UsageOverTime
          data={data}
          limit={limit}
          isBillingPeriod={hasBillingPeriod}
        />

        <UsageBreakdown
          organisationId={organisationId}
          billingPeriod={billingPeriod}
          data={data}
          projectId={projectId}
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
