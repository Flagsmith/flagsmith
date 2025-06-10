import React, { FC, useEffect, useState } from 'react'
import { Link, NavLink, useHistory, useLocation } from 'react-router-dom'
import BreadcrumbSeparator from './BreadcrumbSeparator'
import classNames from 'classnames'
import AccountStore from 'common/stores/account-store'
import GithubStar from './GithubStar'
import Icon from './Icon'
import Headway from './Headway'
import NavSubLink from './NavSubLink'
import { apps, gitBranch, gitCompare, statsChart } from 'ionicons/icons'
import SegmentsIcon from './svg/SegmentsIcon'
import Permission from 'common/providers/Permission'
import AuditLogIcon from './svg/AuditLogIcon'
import SettingsIcon from './svg/SettingsIcon'
import UsersIcon from './svg/UsersIcon'
import HomeAside from './pages/HomeAside'
import Utils from 'common/utils/utils'
import { useGetProfileQuery } from 'common/services/useProfile'
import { Project as ProjectType } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import Project from 'common/project'
import Tooltip from './Tooltip'
import OverflowNav from './OverflowNav'
type NavType = {
  environmentId: string | undefined
  projectId: number
  activeProject: ProjectType | undefined
}

const Nav: FC<NavType> = ({
  activeProject,
  children,
  environmentId,
  projectId,
}) => {
  const { data: user } = useGetProfileQuery({})
  const [lastEnvironmentId, setLastEnvironmentId] = useState()
  const [lastProjectId, setLastProjectId] = useState()

  const isOrganisationSelect = document.location.pathname === '/organisations'
  const integrations = Object.keys(Utils.getIntegrationData())
  const history = useHistory()
  const location = useLocation()
  const pathname = location.pathname
  const [asideIsVisible, setAsideIsVisible] = useState()

  useEffect(() => {
    const updateLastViewed = () => {
      AsyncStorage.getItem('lastEnv').then((res) => {
        if (res) {
          const lastEnv = JSON.parse(res)
          setLastEnvironmentId(lastEnv.environmentId)
          setLastProjectId(lastEnv.projectId)
        }
      })
    }
    const unlisten = history.listen(updateLastViewed)
    updateLastViewed()
    return () => unlisten()
  }, [history])

  const isCreateEnvironment = environmentId === 'create'
  const isCreateOrganisation = document.location.pathname === '/create'
  const storageHasParams = lastEnvironmentId || lastProjectId
  const pageHasAside = environmentId || projectId || storageHasParams
  const isHomepage =
    pathname === '/' ||
    pathname === '/login' ||
    pathname === '/signup' ||
    pathname === '/github-setup' ||
    pathname.includes('/invite')
  return (
    <div className='fs-small'>
      <div>
        {!isHomepage && (!pageHasAside || !asideIsVisible) && (
          <div className='d-flex py-0'>
            <Flex className='flex-row px-3 bg-faint'>
              {user ? (
                <React.Fragment>
                  <nav className='mt-2 mb-1 space flex-row hidden-xs-down'>
                    <Row className='gap-2'>
                      <Link data-test='home-link' to={'/organisations'}>
                        <img
                          style={{
                            height: 24,
                            width: 24,
                          }}
                          src='/static/images/nav-logo.png'
                        />
                      </Link>
                      {!(isOrganisationSelect || isCreateOrganisation) && (
                        <div className='d-flex gap-1 ml-1 align-items-center'>
                          <div
                            className={
                              !!activeProject && !!projectId
                                ? 'd-none d-md-block'
                                : ''
                            }
                          >
                            <BreadcrumbSeparator
                              projectId={projectId}
                              hideSlash={!activeProject}
                              focus='organisation'
                            >
                              <NavLink
                                id='organisation-link'
                                data-test='organisation-link'
                                activeClassName='active'
                                className={classNames('breadcrumb-link', {
                                  active: !projectId,
                                })}
                                to={Utils.getOrganisationHomePage()}
                              >
                                <div>
                                  {AccountStore.getOrganisation()?.name}
                                </div>
                              </NavLink>
                            </BreadcrumbSeparator>
                          </div>
                          {!!activeProject && !!projectId && (
                            <BreadcrumbSeparator
                              projectId={projectId}
                              hideSlash
                              focus='project'
                            >
                              <NavLink
                                to={`/project/${activeProject.id}`}
                                id='project-link'
                                activeClassName='active'
                                className={'breadcrumb-link active'}
                              >
                                <div>{activeProject.name}</div>
                              </NavLink>
                            </BreadcrumbSeparator>
                          )}
                        </div>
                      )}
                    </Row>
                    <Row className='align-items-center'>
                      <GithubStar />
                      <Tooltip
                        place='bottom'
                        title={
                          Utils.getFlagsmithHasFeature('welcome_page') ? (
                            <NavLink
                              activeClassName='active'
                              to={'/getting-started'}
                              className='d-flex px-3 text-end lh-1 align-items-center'
                            >
                              <span>
                                <Icon
                                  name='file-text'
                                  width={20}
                                  fill='#9DA4AE'
                                />
                              </span>
                            </NavLink>
                          ) : (
                            <a
                              className='d-flex ps-3 text-end lh-1 align-items-center'
                              href={'https://docs.flagsmith.com'}
                            >
                              <span>
                                <Icon
                                  name='file-text'
                                  width={20}
                                  fill='#9DA4AE'
                                />
                              </span>
                            </a>
                          )
                        }
                      >
                        {'Docs'}
                      </Tooltip>
                      <Headway className='cursor-pointer' />
                      <Tooltip
                        place='bottom'
                        title={
                          <NavLink
                            className='d-flex ps-3 lh-1 align-items-center'
                            id='account-settings-link'
                            data-test='account-settings-link'
                            activeClassName='active'
                            to={'/account'}
                          >
                            <span className='mr-1'>
                              <Icon name='person' width={20} fill='#9DA4AE' />
                            </span>
                          </NavLink>
                        }
                      >
                        {'Account'}
                      </Tooltip>
                    </Row>
                  </nav>
                </React.Fragment>
              ) : (
                <div />
              )}
            </Flex>
          </div>
        )}
        {!isOrganisationSelect && !isCreateOrganisation && (
          <OverflowNav
            gap={2}
            key={activeProject ? 'project' : 'organisation'}
            containerClassName='px-2 bg-faint'
            className='py-0 gap-md-4 d-flex'
          >
            {activeProject ? (
              <>
                <NavSubLink
                  icon={gitBranch}
                  className={environmentId ? 'active' : ''}
                  id={`features-link`}
                  to={`/project/${projectId}/environment/${
                    lastEnvironmentId || environmentId
                  }/features`}
                >
                  Environments
                </NavSubLink>
                <NavSubLink
                  icon={<SegmentsIcon />}
                  id={`segments-link`}
                  to={`/project/${projectId}/segments`}
                >
                  Segments
                </NavSubLink>
                <Permission
                  level='project'
                  permission='VIEW_AUDIT_LOG'
                  id={projectId}
                >
                  {({ permission }) =>
                    permission && (
                      <NavSubLink
                        icon={<AuditLogIcon />}
                        id='audit-log-link'
                        to={`/project/${projectId}/audit-log`}
                        data-test='audit-log-link'
                      >
                        Audit Log
                      </NavSubLink>
                    )
                  }
                </Permission>
                {!!integrations.length && (
                  <NavSubLink
                    icon={<Icon name='layers' />}
                    id='integrations-link'
                    to={`/project/${projectId}/integrations`}
                  >
                    Integrations
                  </NavSubLink>
                )}
                <NavSubLink
                  icon={gitCompare}
                  id='compare-link'
                  to={`/project/${projectId}/compare`}
                >
                  Compare
                </NavSubLink>
                <Permission level='project' permission='ADMIN' id={projectId}>
                  {({ permission }) =>
                    permission && (
                      <NavSubLink
                        icon={<SettingsIcon />}
                        id='project-settings-link'
                        to={`/project/${projectId}/settings`}
                      >
                        Project Settings
                      </NavSubLink>
                    )
                  }
                </Permission>
              </>
            ) : (
              !!AccountStore.getOrganisation() && (
                <>
                  <NavSubLink
                    icon={apps}
                    id='projects-link'
                    to={Utils.getOrganisationHomePage()}
                  >
                    Projects
                  </NavSubLink>
                  <NavSubLink
                    data-test='users-and-permissions'
                    icon={<UsersIcon />}
                    id='permissions-link'
                    to={`/organisation/${
                      AccountStore.getOrganisation().id
                    }/permissions`}
                  >
                    Users and Permissions
                  </NavSubLink>
                  {!Project.disableAnalytics && AccountStore.isAdmin() && (
                    <NavSubLink
                      icon={statsChart}
                      id='permissions-link'
                      to={`/organisation/${
                        AccountStore.getOrganisation().id
                      }/usage`}
                    >
                      Usage
                    </NavSubLink>
                  )}
                  {AccountStore.isAdmin() && (
                    <>
                      {Utils.getFlagsmithHasFeature(
                        'organisation_integrations',
                      ) && (
                        <NavSubLink
                          icon={<Icon name='layers' />}
                          id='integrations-link'
                          to={`/organisation/${
                            AccountStore.getOrganisation().id
                          }/integrations`}
                        >
                          Organisation Integrations
                        </NavSubLink>
                      )}
                      <NavSubLink
                        icon={<SettingsIcon />}
                        id='org-settings-link'
                        data-test='org-settings-link'
                        to={`/organisation/${
                          AccountStore.getOrganisation().id
                        }/settings`}
                      >
                        Organisation Settings
                      </NavSubLink>
                    </>
                  )}
                </>
              )
            )}
          </OverflowNav>
        )}
        <hr className='my-0 py-0' />
        {environmentId && !isCreateEnvironment ? (
          <div className='d-md-flex'>
            <HomeAside
              history={history}
              environmentId={environmentId}
              projectId={projectId}
            />
            <div className='aside-container'>{children}</div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )
}

export default Nav
