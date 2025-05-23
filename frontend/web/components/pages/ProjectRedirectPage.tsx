import { FC, useEffect } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useHistory, useRouteMatch } from 'react-router'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'

interface RouteParams {
  projectId: string
}

const ProjectRedirectPage: FC = () => {
  const history = useHistory()
  const match = useRouteMatch<RouteParams>()
  const projectId = match?.params?.projectId

  const { data, error } = useGetEnvironmentsQuery({ projectId })
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
        `/project/${projectId}/environment/${environment.api_key}/features`,
      )
    } else {
      history.replace(`/project/${projectId}/environment/create`)
    }
  }, [data, error, history])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
