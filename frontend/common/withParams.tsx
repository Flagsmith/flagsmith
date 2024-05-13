import { matchPath } from 'react-router'
import get from 'lodash/get'
import AccountStore from './stores/account-store'
import { withRouter } from 'react-router-dom'
import { FC } from 'react'

function getProjectId() {
  const location = document.location
  const pathname = location.pathname
  const match = matchPath(pathname, {
    exact: false,
    path: '/project/:projectId/environment/:environmentId',
    strict: false,
  })
  const match2 = matchPath(pathname, {
    exact: false,
    path: '/project/:projectId',
    strict: false,
  })
  const projectId =
    get(match, 'params.projectId') || get(match2, 'params.projectId')
  return projectId ? parseInt(projectId) : null
}

export function getEnvironmentId() {
  const location = document.location
  const pathname = location.pathname

  const match = matchPath(pathname, {
    exact: false,
    path: '/project/:projectId/environment/:environmentId',
    strict: false,
  })

  const environmentId = get(match, 'params.environmentId')
  return environmentId || null
}
export function getOrganisationIdFromPath() {
  const location = document.location
  const pathname = location.pathname

  const match = matchPath(pathname, {
    exact: false,
    path: '/organisation/:organisationId',
    strict: false,
  })
  const storeId = AccountStore.getOrganisationIdFromPath()
  const organisationId = get(match, 'params.organisationId')
  return organisationId ? parseInt(organisationId) : storeId
}
export type WithParamsProps = {
  organisationId: number | null
  projectId: number | null
  environmentId: number | null
}
export default function withParams(WrappedComponent: any) {
  const HOC: FC<WithParamsProps> = (props) => {
    const organisationId = getOrganisationIdFromPath()
    const projectId = getProjectId()

    const environmentId = getEnvironmentId()
    return (
      <WrappedComponent
        {...props}
        organisationId={organisationId}
        environmentId={environmentId}
        projectId={projectId}
      />
    )
  }

  return withRouter(HOC as any)
}
