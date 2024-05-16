import { FC, useEffect } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { RouterChildContext } from 'react-router'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'

type ProjectRedirectPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      projectId: string
    }
  }
}

const ProjectRedirectPage: FC<ProjectRedirectPageType> = ({
  match: {
    params: { projectId },
  },
  router,
}) => {
  const { data, error } = useGetEnvironmentsQuery({ projectId })
  useEffect(() => {
    if (!data) {
      return
    }
    if (error) {
      router.history.replace(Utils.getOrganisationHomePage())
    }
    const environment = data?.results?.[0]
    if (environment) {
      router.history.replace(
        `/project/${projectId}/environment/${environment.api_key}/features`,
      )
    } else {
      router.history.replace(`/project/${projectId}/environment/create`)
    }
  }, [data, error])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(ProjectRedirectPage)
