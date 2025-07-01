import React, { FC, ReactNode, useEffect, useState } from 'react'
import { NavLink, useHistory, useLocation } from 'react-router-dom'
import AccountStore from 'common/stores/account-store'
import HomeAside from './EnvironmentAside'
import { Project as ProjectType } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import ProjectNav from './ProjectNav'
import OrganisationNav from './OrganisationNav'
import SelectOrgAndProject from './SelectOrgAndProject'
import Utils from 'common/utils/utils'
import GithubStar from 'components/GithubStar'
import Icon from 'components/Icon'
import Headway from 'components/Headway'

type NavType = {
  environmentId: string | undefined
  projectId: number
  header?: ReactNode
  activeProject: ProjectType | undefined
}

const Nav: FC<NavType> = ({
  activeProject,
  children,
  environmentId,
  header,
  projectId,
}) => {
  const [lastEnvironmentId, setLastEnvironmentId] = useState()
  const [lastProjectId, setLastProjectId] = useState()

  const isOrganisationSelect = document.location.pathname === '/organisations'
  const history = useHistory()
  const location = useLocation()
  const pathname = location.pathname

  useEffect(() => {
    const updateLastViewed = () => {
      AsyncStorage.getItem('lastEnv').then((res: string | null) => {
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
  const isHomepage =
    pathname === '/' ||
    pathname === '/login' ||
    pathname === '/signup' ||
    pathname === '/github-setup' ||
    pathname.includes('/invite')

  const showNav =
    !isOrganisationSelect &&
    !isCreateOrganisation &&
    !!AccountStore.getOrganisation()?.id

  return (
    <div className='fs-small'>
      <div>
        {!isHomepage && (
          <div className='d-flex bg-faint pt-1 py-0'>
            <Flex className='flex-row px-2 '>
              {!!AccountStore.getUser() && (
                <React.Fragment>
                  <nav className='mt-2 mb-1 space flex-row hidden-xs-down'>
                    <SelectOrgAndProject
                      activeProject={activeProject}
                      projectId={projectId}
                    />
                    <Row className='align-items-center'>
                      <div className='me-3'>
                        <GithubStar />
                      </div>
                      {Utils.getFlagsmithHasFeature('welcome_page') && (
                        <NavLink
                          activeClassName='active'
                          to={'/getting-started'}
                          className='d-flex gap-1 d-none d-md-flex text-end lh-1 align-items-center'
                        >
                          <span>
                            <Icon name='rocket' width={20} fill='#9DA4AE' />
                          </span>
                          <span className='d-none d-md-block'>
                            Getting Started
                          </span>
                        </NavLink>
                      )}
                      <a
                        className='d-flex gap-1 ps-3 text-end lh-1 align-items-center'
                        href={'https://docs.flagsmith.com'}
                      >
                        <span>
                          <Icon name='file-text' width={20} fill='#9DA4AE' />
                        </span>
                        <span className='d-none d-md-block'>Docs</span>
                      </a>
                      <Headway className='cursor-pointer' />

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
                        <span className='d-none d-md-block'>Account</span>
                      </NavLink>
                    </Row>
                  </nav>
                </React.Fragment>
              )}
            </Flex>
          </div>
        )}
        {showNav && (
          <>
            {activeProject ? (
              <ProjectNav
                projectId={projectId || lastProjectId}
                environmentId={environmentId || lastEnvironmentId}
              />
            ) : (
              <OrganisationNav />
            )}
          </>
        )}
        <hr className='my-0 py-0' />
        {environmentId && !isCreateEnvironment ? (
          <div className='d-md-flex'>
            <div>
              <HomeAside
                history={history}
                environmentId={environmentId}
                projectId={projectId}
              />
            </div>
            <div className='aside-container'>
              <div>{header}</div>
              {children}
            </div>
          </div>
        ) : (
          <div>
            <div>{header}</div>
            {children}
          </div>
        )}
      </div>
    </div>
  )
}

export default Nav
