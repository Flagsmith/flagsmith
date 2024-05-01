import React, { FC } from 'react'
import ProjectManageWidget from './ProjectManageWidget'
import AccountProvider from 'common/providers/AccountProvider'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import { Organisation } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'
import PageTitle from './PageTitle'

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
            <ProjectManageWidget organisationId={match.params.organisationId} />
          </div>
        )
      }}
    </OrganisationProvider>
  )
}

export default ConfigProvider(ProjectsPage)
