import { FC, ReactNode } from 'react'
import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import SectionHeading from './SectionHeading'
import UsageOverTime from './UsageOverTime'

export type UsageExplorerProps = {
  data: Res['organisationUsage'] | undefined
  /** The ceiling to draw, or nothing when the view is not comparable. */
  limit: PlanLimit
  isBillingPeriod: boolean
  periodLabel: string
  isLoading?: boolean
  filters?: ReactNode
  breakdown?: ReactNode
}

// Its own loading state keeps the meter above it still while a period loads.
const UsageExplorer: FC<UsageExplorerProps> = ({
  breakdown,
  data,
  filters,
  isBillingPeriod,
  isLoading,
  limit,
  periodLabel,
}) => (
  <>
    <SectionHeading
      title='Explore usage'
      hint='Narrow the chart and the breakdown by period or project.'
      action={filters}
    />

    {isLoading ? (
      <div className='text-center py-5'>
        <Loader />
      </div>
    ) : (
      <>
        <UsageOverTime
          data={data}
          limit={limit}
          isBillingPeriod={isBillingPeriod}
          periodLabel={periodLabel}
        />

        {breakdown}
      </>
    )}
  </>
)

export default UsageExplorer
