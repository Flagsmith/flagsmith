import { FC, useState } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'
import Utils, { planNames } from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import UsageChartFilters from 'components/organisation-settings/usage/components/UsageChartFilters'
import UsageBillingPrototype from 'components/organisation-settings/usage/UsageBillingPrototype'

const OrganisationUsagePage: FC = () => {
  const { organisationId } = useRouteContext()

  const [project, setProject] = useState<string | undefined>()
  const [environment, setEnvironment] = useState<string | undefined>()

  const currentPlan = Utils.getPlanName(AccountStore.getActiveOrgPlan())
  const orgSubscription = AccountStore.getOrganisation()?.subscription
  const isOnFreePlanPeriods =
    planNames.free === currentPlan ||
    !orgSubscription?.has_active_billing_periods

  const [billingPeriod, setBillingPeriod] = useState<
    Req['getOrganisationUsage']['billing_period']
  >(isOnFreePlanPeriods ? '90_day_period' : 'current_billing_period')

  // Option A: the plan limit is org-level, so the meter + cumulative chart
  // always use org-wide usage (period only). Project/Environment refine the
  // breakdown, so it gets its own filtered query.
  const { data: orgData } = useGetOrganisationUsageQuery(
    { billing_period: billingPeriod, organisationId: organisationId || 0 },
    { skip: !organisationId },
  )
  const { data: filteredData } = useGetOrganisationUsageQuery(
    {
      billing_period: billingPeriod,
      environmentId: environment,
      organisationId: organisationId || 0,
      projectId: project,
    },
    { skip: !organisationId },
  )

  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery(
    { id: organisationId || 0 },
    { skip: !organisationId },
  )

  return (
    <div className='app-container px-3 px-md-4 pb-4'>
      <UsageChartFilters
        organisationId={organisationId || 0}
        project={project}
        setProject={setProject}
        environment={environment}
        setEnvironment={setEnvironment}
        billingPeriod={billingPeriod}
        setBillingPeriod={setBillingPeriod}
        isOnFreePlanPeriods={isOnFreePlanPeriods}
      />
      {/* SPIKE: billing-aligned usage redesign prototype. */}
      <UsageBillingPrototype
        data={orgData}
        breakdownData={filteredData}
        maxApiCalls={subscriptionMeta?.max_api_calls}
      />
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
