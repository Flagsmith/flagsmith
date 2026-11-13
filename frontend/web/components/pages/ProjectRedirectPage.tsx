import { FC } from 'react'
import { Redirect } from 'react-router-dom'
import { useEnvironmentsByName } from 'common/hooks/useEnvironmentsByName'
import Utils from 'common/utils/utils'
import { getProjectLandingPath } from 'common/utils/projectLandingPath'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'

const ProjectRedirectPage: FC = () => {
  const { projectId } = useRouteContext()
  const { environments, isError } = useEnvironmentsByName(projectId)

  if (isError) {
    return <Redirect to={Utils.getOrganisationHomePage()} />
  }
  if (projectId && environments) {
    return <Redirect to={getProjectLandingPath(projectId, environments)} />
  }
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
