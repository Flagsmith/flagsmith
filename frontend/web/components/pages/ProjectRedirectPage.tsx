import { FC } from 'react'
import { Redirect } from 'react-router-dom'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'
import Utils from 'common/utils/utils'
import { getProjectLandingPath } from 'common/utils/projectLandingPath'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'

const ProjectRedirectPage: FC = () => {
  const { projectId } = useRouteContext()
  const { data, isError } = useGetAllEnvironmentsQuery(
    projectId ? { projectId } : skipToken,
  )

  if (isError) {
    return <Redirect to={Utils.getOrganisationHomePage()} />
  }
  if (projectId && data) {
    return (
      <Redirect
        to={getProjectLandingPath(projectId, sortEnvironmentsByName(data))}
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
