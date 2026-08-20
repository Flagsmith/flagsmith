import { FC, ReactNode } from 'react'
import { Res } from 'common/types/responses'
import UsageDashboardBody from './UsageDashboardBody'

export type UsageDashboardViewProps = {
  data: Res['organisationUsage'] | undefined
  total: number
  limit: number | null | undefined
  /**
   * Whether the selected period accumulates towards the limit. False for the
   * rolling windows, and for any plan without a billing term.
   */
  hasBillingPeriod: boolean
  isError?: boolean
  isLoading?: boolean
  /** A slot, because the controls fetch their own options. */
  filters?: ReactNode
}

/** Kept apart from the fetching so every state can be rendered on its own. */
const UsageDashboardView: FC<UsageDashboardViewProps> = ({
  filters,
  ...body
}) => (
  <div className='px-3 px-md-4 py-4'>
    <Row space className='mb-4 align-items-center'>
      <h4 className='mb-0'>Usage</h4>
      {filters}
    </Row>

    <UsageDashboardBody {...body} />
  </div>
)

export default UsageDashboardView
