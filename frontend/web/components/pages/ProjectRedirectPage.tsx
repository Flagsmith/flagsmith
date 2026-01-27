import { FC, useEffect } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useHistory, useLocation } from 'react-router-dom'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'

const ProjectRedirectPage: FC = () => {
  const history = useHistory()
  const location = useLocation()
  const { projectId } = useRouteContext()

  const { data, error } = useGetEnvironmentsQuery({
    projectId: projectId?.toString() || '',
  })
  useEffect(() => {
    if (!data) {
      return
    }
    if (error) {
      history.replace(Utils.getOrganisationHomePage())
    }
    const environment = data?.results?.[0]
    if (environment) {
      history.replace(
        `/project/${projectId}/environment/${environment.api_key}/features${location.search}`,
      )
    } else {
      history.replace(`/project/${projectId}/environment/create`)
    }
  }, [data, error, history, location.search])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
