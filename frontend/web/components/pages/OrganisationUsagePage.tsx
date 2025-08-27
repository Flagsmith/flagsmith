import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import OrganisationUsage from 'components/organisation-settings/usage/OrganisationUsage.container'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useLocation, useRouteMatch } from 'react-router-dom'
import OrganisationUsageMetrics from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import OrganisationUsageSideBar from 'components/organisation-settings/usage/components/OrganisationUsageSideBar'
import { useRouteContext } from 'components/providers/RouteContext'
import { AggregateUsageDataItem } from 'common/types/responses'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { planNames } from 'common/utils/utils'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'

interface RouteParams {
  organisationId: string
}

const OrganisationUsagePage: FC = () => {
  const { organisationId } = useRouteContext()
  const match = useRouteMatch<RouteParams>()
  const location = useLocation()

  const getInitialView = useCallback((): 'global' | 'metrics' => {
    const params = new URLSearchParams(location.search)
    return params.get('p') === 'metrics' ? 'metrics' : 'global'
  }, [location.search])

  const [chartsView, setChartsView] = useState<'global' | 'metrics'>(
    getInitialView(),
  )
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

  console.log('Query params:', {
    billing_period: billingPeriod,
    environmentId: environment,
    organisationId: organisationId?.toString() || '',
    projectId: project,
  })

  const { data, isError } = useGetOrganisationUsageQuery(
    {
      billing_period: billingPeriod,
      environmentId: environment,
      organisationId: organisationId?.toString() || '',
      projectId: project,
    },
    { skip: !organisationId },
  )
  console.log('Query result:', { data, isError })

  // Aggregate usage events by date, summing metrics across all client types
  const consolidatedDailyUsage = useMemo(() => {
    console.log('recomputing')
    return Object.values(
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
  }, [data?.events_list])
  console.log('consolidatedDailyUsage', consolidatedDailyUsage?.length)
  useEffect(() => {
    const currentView = getInitialView()
    if (currentView !== chartsView) {
      setChartsView(currentView)
    }
  }, [location.search, chartsView, getInitialView])

  // Shared usage data props
  const usageDataProps = {
    billingPeriod,
    consolidatedDailyUsage,
    data,
    environment,
    isError,
    isOnFreePlanPeriods,
    project,
    setBillingPeriod,
    setEnvironment,
    setProject,
  }
  return (
    <div className='app-container px-3 px-md-0 pb-2'>
      <Row className='grid-container gap-x-3'>
        <div className='col-12 col-md-2 border-md-right home-aside aside-small d-flex flex-column'>
          <div style={{ maxWidth: '200px' }}>
            {organisationId && (
              <OrganisationUsageSideBar
                organisationId={organisationId}
                activeTab={chartsView}
              />
            )}
          </div>
        </div>
        <div className='col-12 col-md-8'>
          {chartsView === 'metrics' ? (
            <OrganisationUsageMetrics />
          ) : (
            <OrganisationUsage
              organisationId={match.params.organisationId}
              data={data}
              isError={isError}
              consolidatedDailyUsage={consolidatedDailyUsage}
              project={project}
              setProject={setProject}
              environment={environment}
              setEnvironment={setEnvironment}
              billingPeriod={billingPeriod}
              setBillingPeriod={setBillingPeriod}
              isOnFreePlanPeriods={isOnFreePlanPeriods}
            />
          )}
        </div>
      </Row>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
