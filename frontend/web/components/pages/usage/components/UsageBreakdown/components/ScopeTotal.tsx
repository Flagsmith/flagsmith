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
  onTotal: (key: string, total: number | null | undefined) => void
}

/**
 * Fetches one scope's total. The endpoint filters by project and environment
 * rather than grouping, so a breakdown needs one request per key, and it
 * cannot be a loop of hooks: the key list changes length between renders.
 */
const ScopeTotal: FC<ScopeTotalProps> = ({
  billingPeriod,
  onTotal,
  organisationId,
  scope,
}) => {
  const { data, isError } = useGetOrganisationUsageQuery({
    billing_period: billingPeriod,
    environmentId: scope.environmentId,
    organisationId,
    projectId: scope.projectId,
  })

  // null distinguishes answered-with-nothing from still in flight.
  const total = isError ? null : data?.totals?.total

  useEffect(() => {
    onTotal(scope.key, total)
  }, [scope.key, total, onTotal])

  return null
}

export default ScopeTotal
