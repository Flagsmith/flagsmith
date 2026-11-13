import React, { FC, ReactNode, useEffect, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import AccountStore from 'common/stores/account-store'
import EnvironmentAside from './EnvironmentAside'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetProjectQuery } from 'common/services/useProject'
import EmptyState from 'components/EmptyState'
import { AsyncStorage } from 'polyfill-react-native'
import ProjectNavbar from './navbars/ProjectNavbar'
import OrganisationNavbar from './navbars/OrganisationNavbar'
import TopNavbar from './navbars/TopNavbar'
import { appLevelPaths } from './constants'

type NavType = {
  environmentId: string | undefined
  projectId: number
  header?: ReactNode
}

const Nav: FC<NavType> = ({ children, environmentId, header, projectId }) => {
  const [lastEnvironmentId, setLastEnvironmentId] = useState()
  const [lastProjectId, setLastProjectId] = useState()

  const isAppLevelPage = appLevelPaths.includes(document.location.pathname)
  const history = useHistory()
  const location = useLocation()
  const pathname = location.pathname

  const {
    currentData: activeProject,
    isError: isProjectError,
    refetch: refetchProject,
  } = useGetProjectQuery(projectId ? { id: projectId } : skipToken)
  const isProjectPage = pathname.includes('project/')
  let content = children
  if (isProjectPage && isProjectError) {
    content = (
      <div className='container mt-4'>
        <EmptyState
          status='error'
          title='Could not load this project'
          onRetry={refetchProject}
        />
      </div>
    )
  } else if (isProjectPage && !activeProject) {
    content = (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

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
  const isHomepage =
    pathname === '/' ||
    pathname === '/login' ||
    pathname === '/signup' ||
    pathname === '/github-setup' ||
    pathname.includes('/invite')

  // Check if we're on a persona view page where nav should be hidden
  const isPersonaViewPage =
    pathname.includes('/release-manager') ||
    pathname.includes('/executive-view') ||
    pathname.includes('/dev-view') ||
    /\/project\/\d+\/flag\/\d+\/environments/.test(pathname)

  const showNav =
    !isAppLevelPage &&
    !isPersonaViewPage &&
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
                <EnvironmentAside
                  history={history}
                  environmentId={environmentId}
                  projectId={projectId}
                />
              </div>
              <div className='aside-container'>
                <div className='d-none d-md-block'>{header}</div>
                {content}
              </div>
            </div>
          </>
        ) : (
          <div>
            <div>{header}</div>
            {content}
          </div>
        )}
      </div>
    </div>
  )
}

export default Nav
