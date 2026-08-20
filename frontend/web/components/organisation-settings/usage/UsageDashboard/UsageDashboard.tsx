import { FC, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import ProjectFilter from 'components/ProjectFilter'
import { PeriodOption } from 'common/types/requests'
import UsageDashboardView from './UsageDashboardView'
import {
  hasBillingPeriod as deriveHasBillingPeriod,
  periodsFor,
  PeriodSelection,
  resolvePeriod,
} from './utils'
import './UsageDashboard.scss'

type UsageDashboardProps = {
  /** Absent until the route context resolves, so nothing is drawn yet. */
  organisationId: number | undefined
}

/** Behind `usage_dashboard`. Owns the fetching; the view draws the result. */
const UsageDashboard: FC<UsageDashboardProps> = ({ organisationId }) => {
  const [project, setProject] = useState<string | undefined>()

  const { data: organisation } = useGetOrganisationQuery(
    organisationId ? { id: organisationId } : skipToken,
  )
  const subscription = organisation?.subscription
  const isFreePlan =
    planNames.free === Utils.getPlanName(subscription?.plan ?? '')
  const hasBillingPeriod = deriveHasBillingPeriod(subscription, isFreePlan)

  const [chosenPeriod, setChosenPeriod] = useState<PeriodSelection>('default')
  const billingPeriod = resolvePeriod(chosenPeriod, hasBillingPeriod)

  const { data, isError, isLoading } = useGetOrganisationUsageQuery(
    organisationId
      ? {
          billing_period: billingPeriod,
          organisationId,
          // ProjectFilter hands the id back as a string, the query wants the pk.
          projectId: project ? Number(project) : undefined,
        }
      : skipToken,
  )
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery(
    organisationId ? { id: organisationId } : skipToken,
  )

  const periods = periodsFor(hasBillingPeriod)

  if (!organisationId) {
    return null
  }

  return (
    <UsageDashboardView
      data={data}
      total={data?.totals?.total ?? 0}
      limit={subscriptionMeta?.max_api_calls}
      hasBillingPeriod={hasBillingPeriod}
      isError={isError}
      isLoading={isLoading}
      filters={
        <Row className='gap-2'>
          <div className='usage-dashboard__filter'>
            <Select
              onChange={(option: PeriodOption) => setChosenPeriod(option.value)}
              value={periods.find((period) => period.value === billingPeriod)}
              options={periods}
            />
          </div>
          <div className='usage-dashboard__filter'>
            <ProjectFilter
              showAll
              organisationId={organisationId}
              onChange={setProject}
              value={project}
            />
          </div>
        </Row>
      }
    />
  )
}

export default UsageDashboard
