import { FC, useEffect } from 'react'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'

export type UsageScope = {
  label: string
  projectId?: number
  environmentId?: string
}

type UsageScopeTotalProps = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  scope: UsageScope
  onTotal: (label: string, total: number | undefined) => void
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
 * A `group_by` on the endpoint would collapse all of this into one request.
 */
const UsageScopeTotal: FC<UsageScopeTotalProps> = ({
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
    onTotal(scope.label, total)
  }, [scope.label, total, onTotal])

  return null
}

export default UsageScopeTotal
