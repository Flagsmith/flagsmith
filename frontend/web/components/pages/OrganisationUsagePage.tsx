import { FC, useCallback, useEffect, useState } from 'react'
import OrganisationUsage from 'components/organisation-settings/usage/OrganisationUsage.container'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useLocation, useRouteMatch } from 'react-router-dom'
import OrganisationUsageMetrics from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'
import OrganisationUsageSideBar from 'components/organisation-settings/usage/components/OrganisationUsageSideBar'
import { useRouteContext } from 'components/providers/RouteContext'

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
  useEffect(() => {
    const currentView = getInitialView()
    if (currentView !== chartsView) {
      setChartsView(currentView)
    }
  }, [location.search, chartsView, getInitialView])

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
            <OrganisationUsage organisationId={match.params.organisationId} />
          )}
        </div>
      </Row>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
