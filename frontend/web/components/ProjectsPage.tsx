import React, { FC } from 'react'
import ProjectManageWidget from './ProjectManageWidget'
import AccountProvider from 'common/providers/AccountProvider'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import { Organisation } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'

type ProjectsPageType = {
  match: {
    params: {
      organisationId: string
    }
  }
}
const ProjectsPage: FC<ProjectsPageType> = ({ match }) => {
  return (
    <OrganisationProvider id={match.params.organisationId}>
      {() => {
        return (
          <div className='app-container container'>
            <h5 className='mt-4 mb-2'>Projects</h5>

            <p className='fs-small lh-sm mb-4'>
              Projects let you create and manage a set of features and configure
              them between multiple app environments.
            </p>
            <ProjectManageWidget organisationId={match.params.organisationId} />
          </div>
        )
      }}
    </OrganisationProvider>
  )
}

export default ConfigProvider(ProjectsPage)
