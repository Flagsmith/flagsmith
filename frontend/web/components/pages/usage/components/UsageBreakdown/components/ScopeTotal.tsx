import { FC, useEffect } from 'react'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'

export type UsageScope = {
  /** Unique within a dimension. Names repeat, ids do not. */
  key: string
  label: string
  projectId?: number
  environmentId?: string
}

type ScopeTotalProps = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  scope: UsageScope
  onTotal: (key: string, total: number | undefined) => void
}

/**
 * Fetches one scope's total and reports it up. It draws nothing.
 *
 * The endpoint filters by project and environment rather than grouping by them,
 * so a breakdown needs one request per key. It cannot be a loop of hooks: the
 * key list starts empty and fills once loaded, and React requires the same
 * hooks in the same order every render. A `group_by` would remove all of this.
 */
const ScopeTotal: FC<ScopeTotalProps> = ({
  billingPeriod,
  onTotal,
  organisationId,
  scope,
}) => {
  const { data } = useGetOrganisationUsageQuery({
    billing_period: billingPeriod,
    environmentId: scope.environmentId,
    organisationId,
    projectId: scope.projectId,
  })

  const total = data?.totals?.total

  useEffect(() => {
    onTotal(scope.key, total)
  }, [scope.key, total, onTotal])

  return null
}

export default ScopeTotal
