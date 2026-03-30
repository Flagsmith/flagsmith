import React, { FC } from 'react'
import AccountStore from 'common/stores/account-store'
import { Link, NavLink } from 'react-router-dom'
import BreadcrumbSeparator from 'components/BreadcrumbSeparator'
import classNames from 'classnames'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { appLevelPaths } from './constants'

type SelectOrgAndProjectType = {
  activeProject: Project | undefined
  projectId?: number
}

const SelectOrgAndProject: FC<SelectOrgAndProjectType> = ({
  activeProject,
  projectId,
}) => {
  const isAppLevelPage = appLevelPaths.includes(document.location.pathname)

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: organisation } = useGetOrganisationQuery(
    { id: organisationId as number },
    { skip: !organisationId },
  )

  return (
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
      {!isAppLevelPage && (
        <div className='d-flex gap-1 ml-1 align-items-center'>
          <div
            className={
              !!activeProject && !!projectId ? 'd-none d-md-block' : ''
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
                  {organisation?.name || AccountStore.getOrganisation()?.name}
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
  )
}

export default SelectOrgAndProject
