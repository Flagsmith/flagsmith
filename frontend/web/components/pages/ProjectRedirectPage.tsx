import { FC } from 'react'
import { Redirect } from 'react-router-dom'
import { useEnvironmentsByName } from 'common/hooks/useEnvironmentsByName'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'

const ProjectRedirectPage: FC = () => {
  const { projectId } = useRouteContext()
  const { environments, isError } = useEnvironmentsByName(projectId)

  if (isError) {
    return <Redirect to={Utils.getOrganisationHomePage()} />
  }
  if (environments) {
    const environment = environments[0]
    return (
      <Redirect
        to={
          environment
            ? `/project/${projectId}/environment/${environment.api_key}/features`
            : `/project/${projectId}/environment/create`
        }
      />
    )
  }
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
