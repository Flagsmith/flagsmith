import React, { FC } from 'react'
import SelectOrgAndProject from 'components/navigation/SelectOrgAndProject'
import GithubStar from 'components/GithubStar'
import Utils from 'common/utils/utils'
import { NavLink } from 'react-router-dom'
import Icon from 'components/Icon'
import Headway from 'components/Headway'
import { Project } from 'common/types/responses'

type TopNavType = {
  activeProject: Project | undefined
  projectId?: number
}

const TopNavbar: FC<TopNavType> = ({ activeProject, projectId }) => {
  return (
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
              <span className='d-none d-md-block'>Getting Started</span>
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
          <Headway className='cursor-pointer ps-3' />

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
  )
}

export default TopNavbar
