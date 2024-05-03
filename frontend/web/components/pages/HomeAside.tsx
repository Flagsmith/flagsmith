import React, { FC } from 'react'
import ProjectStore from 'common/stores/project-store'
import ChangeRequestStore from 'common/stores/change-requests-store'
import Utils from 'common/utils/utils'
import { Environment, Project } from 'common/types/responses'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import { Link, NavLink } from 'react-router-dom'
import { IonIcon } from '@ionic/react'
import { createOutline } from 'ionicons/icons'
import EnvironmentDropdown from 'components/EnvironmentDropdown'
import Collapsible from 'components/Collapsible'
import ProjectProvider from 'common/providers/ProjectProvider'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import Icon from 'components/Icon'
import { AsyncStorage } from 'polyfill-react-native'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import { RouterChildContext } from 'react-router'
import Constants from 'common/constants'

type HomeAsideType = {
  environmentId: string
  projectId: string
  history: RouterChildContext['router']['history']
}

const HomeAside: FC<HomeAsideType> = ({
  environmentId,
  history,
  projectId,
}) => {
  const environment: Environment | null =
    environmentId === 'create'
      ? null
      : (ProjectStore.getEnvironment(environmentId) as any)
  const hasRbacPermission = Utils.getPlansPermission('AUDIT')
  const changeRequest = Utils.changeRequestsEnabled(
    environment?.minimum_change_request_approvals,
  )
    ? ChangeRequestStore.model[environmentId]
    : null
  const changeRequests = changeRequest?.count || 0
  const scheduled =
    (environment && ChangeRequestStore.scheduled[environmentId]?.count) || 0
  const onProjectSave = () => {
    AppActions.refreshOrganisation()
  }
  return (
    <OrganisationProvider>
      {() => (
        <ProjectProvider id={projectId} onSave={onProjectSave}>
          {({ project }: { project: Project }) => (
            <div className='border-right home-aside'>
              <div className='mt-3'>
                <div className='px-3 mb-2 d-flex align-items-center justify-content-between'>
                  <h6 className='mb-0'>Environments</h6>
                  <Permission
                    level='project'
                    permission='CREATE_ENVIRONMENT'
                    id={projectId}
                  >
                    {({ permission }) =>
                      permission && (
                        <Link
                          id='create-env-link'
                          className='btn btn-xsm d-flex gap-1 align-items-center btn--outline'
                          to={`/project/${projectId}/environment/create`}
                        >
                          <IonIcon className='fs-small' icon={createOutline} />
                          Create
                        </Link>
                      )
                    }
                  </Permission>
                </div>
              </div>
              <EnvironmentDropdown
                renderRow={(environment: Environment, onClick: any) => (
                  <Collapsible
                    data-test={`switch-environment-${environment.name.toLowerCase()}${
                      environmentId === `${environment.api_key}`
                        ? '-active'
                        : ''
                    }`}
                    onClick={onClick}
                    active={environment.api_key === environmentId}
                    title={environment.name}
                  >
                    <Permission
                      level='environment'
                      permission={Utils.getViewIdentitiesPermission()}
                      id={environment.api_key}
                    >
                      {({
                        isLoading: manageIdentityLoading,
                        permission: manageIdentityPermission,
                      }) => (
                        <Permission
                          level='environment'
                          permission='ADMIN'
                          id={environment.api_key}
                        >
                          {({ isLoading, permission: environmentAdmin }) =>
                            isLoading || manageIdentityLoading ? (
                              <div className='text-center'>
                                <Loader />
                              </div>
                            ) : (
                              <div className='list-unstyled aside-nav d-flex flex-column gap-1 ms-3 mb-2 mt-1'>
                                <NavLink
                                  activeClassName='active'
                                  id='features-link'
                                  to={`/project/${project.id}/environment/${environment.api_key}/features`}
                                >
                                  <span className='mr-2'>
                                    <Icon name='rocket' fill='#9DA4AE' />
                                  </span>
                                  Features
                                </NavLink>
                                <NavLink
                                  activeClassName='active'
                                  id='change-requests-link'
                                  to={`/project/${project.id}/environment/${environment.api_key}/scheduled-changes/`}
                                >
                                  <span className='mr-2'>
                                    <Icon name='timer' fill='#9DA4AE' />
                                  </span>
                                  Scheduling
                                  {scheduled ? (
                                    <span className='ml-1 unread d-inline'>
                                      {scheduled}
                                    </span>
                                  ) : null}
                                </NavLink>
                                <NavLink
                                  activeClassName='active'
                                  id='change-requests-link'
                                  to={`/project/${project.id}/environment/${environment.api_key}/change-requests/`}
                                >
                                  <span className='mr-2'>
                                    <Icon name='request' fill='#9DA4AE' />
                                  </span>
                                  Change Requests{' '}
                                  {changeRequests ? (
                                    <span className='unread d-inline'>
                                      {changeRequests}
                                    </span>
                                  ) : null}
                                </NavLink>
                                {environment.use_v2_feature_versioning && (
                                  <NavLink
                                    activeClassName='active'
                                    id='history-link'
                                    to={`/project/${project.id}/environment/${environment.api_key}/history/`}
                                  >
                                    <span className='mr-2'>
                                      <Icon name='clock' fill='#9DA4AE' />
                                    </span>
                                    History
                                  </NavLink>
                                )}
                                {Utils.renderWithPermission(
                                  manageIdentityPermission,
                                  Constants.environmentPermissions(
                                    'View Identities',
                                  ),
                                  <NavLink
                                    id='users-link'
                                    className={`${
                                      !manageIdentityPermission && 'disabled'
                                    }`}
                                    exact
                                    to={`/project/${project.id}/environment/${environment.api_key}/users`}
                                  >
                                    <span className='mr-2'>
                                      <Icon
                                        name='people'
                                        fill={
                                          manageIdentityPermission
                                            ? '#9DA4AE'
                                            : '#696969'
                                        }
                                      />
                                    </span>
                                    Identities
                                  </NavLink>,
                                )}

                                {environmentAdmin && (
                                  <NavLink
                                    id='env-settings-link'
                                    className='aside__environment-list-item'
                                    to={`/project/${project.id}/environment/${environment.api_key}/settings`}
                                  >
                                    <span className='mr-2'>
                                      <Icon name='settings-2' fill='#9DA4AE' />
                                    </span>
                                    Settings
                                  </NavLink>
                                )}
                              </div>
                            )
                          }
                        </Permission>
                      )}
                    </Permission>
                  </Collapsible>
                )}
                projectId={projectId}
                environmentId={environmentId}
                clearableValue={false}
                onChange={(environment: string) => {
                  history.push(
                    `/project/${projectId}/environment/${environment}/features`,
                  )
                  AsyncStorage.setItem(
                    'lastEnv',
                    JSON.stringify({
                      environmentId: environment,
                      orgId: AccountStore.getOrganisation().id,
                      projectId: projectId,
                    }),
                  )
                }}
              />
            </div>
          )}
        </ProjectProvider>
      )}
    </OrganisationProvider>
  )
}

export default ConfigProvider(HomeAside)
