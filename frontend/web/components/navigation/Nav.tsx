import React, { FC, ReactNode, useEffect, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import AccountStore from 'common/stores/account-store'
import HomeAside from './EnvironmentAside'
import { Project as ProjectType } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import ProjectNavbar from './navbars/ProjectNavbar'
import OrganisationNavbar from './navbars/OrganisationNavbar'
import TopNavbar from './navbars/TopNavbar'

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
                <TopNavbar
                  activeProject={activeProject}
                  projectId={projectId}
                />
              )}
            </Flex>
          </div>
        )}
        {showNav && (
          <>
            {activeProject ? (
              <ProjectNavbar
                projectId={projectId || lastProjectId}
                environmentId={environmentId || lastEnvironmentId}
              />
            ) : (
              <OrganisationNavbar />
            )}
          </>
        )}
        <hr className='my-0 py-0' />
        {environmentId && !isCreateEnvironment ? (
          <>
            <div className='d-block d-md-none'>{header}</div>
            <div className='d-md-flex'>
              <div>
                <HomeAside
                  history={history}
                  environmentId={environmentId}
                  projectId={projectId}
                />
              </div>
              <div className='aside-container'>
                <div className='d-none d-md-block'>{header}</div>
                {children}
              </div>
            </div>
          </>
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
