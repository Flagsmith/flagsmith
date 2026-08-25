import { FC, useEffect } from 'react'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import {
  ScopedTotal,
  UsageScope,
} from 'components/pages/usage/components/UsageBreakdown/utils'

type ScopeTotalProps = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  scope: UsageScope
  onTotal: (key: string, total: ScopedTotal) => void
}

const ScopeTotal: FC<ScopeTotalProps> = ({
  billingPeriod,
  onTotal,
  organisationId,
  scope,
}) => {
  const { currentData, isFetching } = useGetOrganisationUsageQuery({
    billing_period: billingPeriod,
    environmentId: scope.environmentId,
    organisationId,
    projectId: scope.projectId,
  })

  const total = isFetching ? undefined : currentData?.totals?.total ?? null

  useEffect(() => {
    onTotal(scope.key, total)
  }, [scope.key, total, onTotal])

  return null
}

export default ScopeTotal
