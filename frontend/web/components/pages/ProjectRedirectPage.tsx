import { FC, useEffect } from 'react'
import sortBy from 'lodash/sortBy'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useHistory } from 'react-router-dom'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'

const ProjectRedirectPage: FC = () => {
  const history = useHistory()
  const { projectId } = useRouteContext()

  const { data, error } = useGetEnvironmentsQuery(
    { projectId: projectId ?? 0 },
    { skip: !projectId },
  )
  useEffect(() => {
    if (error) {
      history.replace(Utils.getOrganisationHomePage())
      return
    }
    if (!data) {
      return
    }
    const environment = sortBy(data.results, 'name')[0]
    if (environment) {
      history.replace(
        `/project/${projectId}/environment/${environment.api_key}/features`,
      )
    } else {
      history.replace(`/project/${projectId}/environment/create`)
    }
  }, [data, error, history, projectId])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
