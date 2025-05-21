import { FC } from 'react'
import OrganisationUsage from 'components/OrganisationUsage'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteMatch } from 'react-router'

interface RouteParams {
  organisationId: string
}

const OrganisationUsagePage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  return (
    <div className='container app-container'>
      <div className='col-xl-8'>
        <OrganisationUsage organisationId={match.params.organisationId} />
      </div>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
