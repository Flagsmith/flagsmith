import React, { FC } from 'react'
import ProjectManageWidget from './ProjectManageWidget'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import ConfigProvider from 'common/providers/ConfigProvider'

type ProjectsPageType = {
  match: {
    params: {
      organisationId: number
    }
  }
}
const ProjectsPage: FC<ProjectsPageType> = ({ match }) => {
  return (
    <OrganisationProvider id={match.params.organisationId}>
      {() => {
        return (
          <div className='app-container container'>
            <ProjectManageWidget
              organisationId={parseInt(match.params.organisationId)}
            />
          </div>
        )
      }}
    </OrganisationProvider>
  )
}

export default ConfigProvider(ProjectsPage)
