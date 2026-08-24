import { FC, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import FieldLabel from 'components/base/forms/FieldLabel'
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

  const {
    data: organisation,
    isError: organisationFailed,
    isLoading: loadingOrganisation,
  } = useGetOrganisationQuery(
    organisationId ? { id: organisationId } : skipToken,
  )
  const subscription = organisation?.subscription
  const isFreePlan =
    planNames.free === Utils.getPlanName(subscription?.plan ?? '')
  const hasBillingPeriod = deriveHasBillingPeriod(subscription, isFreePlan)

  const [chosenPeriod, setChosenPeriod] = useState<PeriodSelection>('default')
  const billingPeriod = resolvePeriod(chosenPeriod, hasBillingPeriod)

  // Waits for the plan. Asking earlier would request the rolling window first,
  // so a billed organisation would show the wrong period and then correct
  // itself, at the cost of an extra request.
  const {
    data,
    isError: usageFailed,
    isLoading: loadingUsage,
  } = useGetOrganisationUsageQuery(
    organisationId && organisation
      ? {
          billing_period: billingPeriod,
          organisationId,
          // ProjectFilter hands the id back as a string, the query wants the pk.
          projectId: project ? Number(project) : undefined,
        }
      : skipToken,
  )
  // Failure is not fatal: no metadata means no limit, which is what a
  // self-hosted installation looks like, and the meter falls back to a count.
  // The wait is another matter. Until it answers the meter would report "no
  // plan limit", which is a claim rather than an absence, and then correct
  // itself a moment later.
  const { data: subscriptionMeta, isLoading: loadingLimit } =
    useGetSubscriptionMetadataQuery(
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
      isError={organisationFailed || usageFailed}
      isLoading={loadingOrganisation || loadingUsage || loadingLimit}
      filters={
        <Row className='gap-3 align-items-end'>
          <div className='usage-dashboard__filter'>
            <FieldLabel htmlFor='usage-period'>Period</FieldLabel>
            <Select
              inputId='usage-period'
              onChange={(option: PeriodOption) => setChosenPeriod(option.value)}
              value={periods.find((period) => period.value === billingPeriod)}
              options={periods}
            />
          </div>
          <div className='usage-dashboard__filter'>
            <FieldLabel htmlFor='usage-project'>Project</FieldLabel>
            <ProjectFilter
              inputId='usage-project'
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
