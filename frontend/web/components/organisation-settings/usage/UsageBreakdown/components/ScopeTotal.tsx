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
 * The endpoint filters by project and environment rather than grouping by
 * them, so a breakdown needs one request per key. Those cannot be a loop of
 * hooks inside the parent: the list of keys starts empty and fills once it
 * loads, and React requires the same hooks in the same order every render. A
 * component per scope keeps each query's lifecycle tied to its own mount.
 *
 * A `group_by` on the endpoint would collapse all of this into one request,
 * and would also remove the wait: the rows only rank correctly once every
 * scope has answered, so the section loads at the pace of its slowest request.
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
