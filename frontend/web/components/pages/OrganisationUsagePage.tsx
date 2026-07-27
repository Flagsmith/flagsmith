import { FC, useCallback, useEffect, useState } from 'react'
import cn from 'classnames'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useLocation } from 'react-router-dom'
import OrganisationUsageMetrics from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import OrganisationUsageSideBar from 'components/organisation-settings/usage/components/OrganisationUsageSideBar'
import { useRouteContext } from 'components/providers/RouteContext'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { planNames } from 'common/utils/utils'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import UsageChartFilters from 'components/organisation-settings/usage/components/UsageChartFilters'
import UsageChartTotals from 'components/organisation-settings/usage/components/UsageChartTotals'
import UsageBillingPrototype from 'components/organisation-settings/usage/UsageBillingPrototype'

const OrganisationUsagePage: FC = () => {
  const isSdkViewEnabled = Utils.getFlagsmithHasFeature('sdk_usage_charts')

  const { organisationId } = useRouteContext()
  const location = useLocation()

  const getInitialView = useCallback((): 'global' | 'user-agents' => {
    if (!isSdkViewEnabled) {
      return 'global'
    }
    const params = new URLSearchParams(location.search)
    return params.get('p') === 'user-agents' ? 'user-agents' : 'global'
  }, [isSdkViewEnabled, location.search])

  const [chartsView, setChartsView] = useState<'global' | 'user-agents'>(
    getInitialView(),
  )
  const [project, setProject] = useState<string | undefined>()
  const [environment, setEnvironment] = useState<string | undefined>()
  const [selection, setSelection] = useState([
    'Flags',
    'Identities',
    'Environment Document',
    'Traits',
  ])

  const colours = ['#0AADDF', '#27AB95', '#FF9F43', '#EF4D56']
  const currentPlan = Utils.getPlanName(AccountStore.getActiveOrgPlan())
  const orgSubscription = AccountStore.getOrganisation()?.subscription
  const isOnFreePlanPeriods =
    planNames.free === currentPlan ||
    !orgSubscription?.has_active_billing_periods

  const [billingPeriod, setBillingPeriod] = useState<
    Req['getOrganisationUsage']['billing_period']
  >(isOnFreePlanPeriods ? '90_day_period' : 'current_billing_period')

  const { data } = useGetOrganisationUsageQuery(
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

  useEffect(() => {
    if (!isSdkViewEnabled) {
      return setChartsView('global')
    }

    const currentView = getInitialView()
    if (currentView !== chartsView) {
      setChartsView(currentView)
    }
  }, [location.search, chartsView, getInitialView, isSdkViewEnabled])

  const updateSelection = (key: string) => {
    if (selection.includes(key)) {
      setSelection(selection.filter((v) => v !== key))
    } else {
      setSelection(selection.concat([key]))
    }
  }

  return (
    <div
      className={cn(
        'app-container',
        isSdkViewEnabled
          ? 'fullwidth-app-container px-3 pb-2 px-md-0 '
          : 'px-12 px-md-5',
      )}
    >
      <Row className='grid-container gap-x-12 align-items-start'>
        {isSdkViewEnabled && (
          <div className='col-12 col-md-2 border-md-right home-aside aside-small d-flex flex-column mx-0'>
            {organisationId && (
              <OrganisationUsageSideBar
                organisationId={organisationId}
                activeTab={chartsView}
              />
            )}
          </div>
        )}
        <div
          className={cn(
            'col-12',
            isSdkViewEnabled ? 'col-md-8 col-lg-9' : 'col-md-12',
          )}
        >
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
          {/* SPIKE: billing-aligned usage redesign prototype.
              Global view renders the reframed design; By SDK keeps the
              existing totals + per-SDK charts. */}
          {chartsView === 'user-agents' ? (
            <>
              <UsageChartTotals
                data={data}
                selection={selection}
                updateSelection={updateSelection}
                colours={colours}
                withColor={false}
                maxApiCalls={subscriptionMeta?.max_api_calls}
              />
              <OrganisationUsageMetrics
                data={data}
                selectedMetrics={selection}
              />
            </>
          ) : (
            <UsageBillingPrototype
              data={data}
              maxApiCalls={subscriptionMeta?.max_api_calls}
            />
          )}
        </div>
      </Row>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
