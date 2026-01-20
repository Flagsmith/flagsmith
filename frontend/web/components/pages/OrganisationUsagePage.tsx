import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import cn from 'classnames'
import OrganisationUsage from 'components/organisation-settings/usage/OrganisationUsage.container'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useLocation } from 'react-router-dom'
import OrganisationUsageMetrics from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import OrganisationUsageSideBar from 'components/organisation-settings/usage/components/OrganisationUsageSideBar'
import { useRouteContext } from 'components/providers/RouteContext'
import { AggregateUsageDataItem } from 'common/types/responses'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { planNames } from 'common/utils/utils'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import UsageChartFilters from 'components/organisation-settings/usage/components/UsageChartFilters'
import UsageChartTotals from 'components/organisation-settings/usage/components/UsageChartTotals'

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

  const { data, isError } = useGetOrganisationUsageQuery(
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

  // Aggregate usage events by date, summing metrics across all client types
  const chartData = useMemo(() => {
    const consolidated = Object.values(
      data?.events_list?.reduce((acc, event) => {
        const date = event.day
        if (!acc[date]) {
          acc[date] = {
            day: date,
            environment_document: 0,
            flags: 0,
            identities: 0,
            traits: 0,
          }
        }

        acc[date].flags = (acc[date].flags ?? 0) + (event.flags ?? 0)
        acc[date].identities =
          (acc[date].identities ?? 0) + (event.identities ?? 0)
        acc[date].traits = (acc[date].traits ?? 0) + (event.traits ?? 0)
        acc[date].environment_document =
          (acc[date].environment_document ?? 0) +
          (event.environment_document ?? 0)

        return acc
      }, {} as Record<string, AggregateUsageDataItem>) || {},
    )

    return consolidated.map((v) => ({
      ...v,
      environment_document: selection.includes('Environment Document')
        ? v.environment_document
        : null,
      flags: selection.includes('Flags') ? v.flags : null,
      identities: selection.includes('Identities') ? v.identities : null,
      traits: selection.includes('Traits') ? v.traits : null,
    }))
  }, [data?.events_list, selection])

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
          <UsageChartTotals
            data={data}
            selection={selection}
            updateSelection={updateSelection}
            colours={colours}
            withColor={chartsView !== 'user-agents'}
            maxApiCalls={subscriptionMeta?.max_api_calls}
          />
          {chartsView === 'user-agents' ? (
            <OrganisationUsageMetrics data={data} selectedMetrics={selection} />
          ) : (
            <OrganisationUsage
              chartData={chartData}
              colours={colours}
              isError={isError}
              selection={selection}
            />
          )}
        </div>
      </Row>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
