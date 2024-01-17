import { FC, useEffect } from 'react'

import Constants from 'common/constants'
import API from 'project/api'

import PageTitle from 'components/PageTitle'
import OrganisationManageWidget from 'components/OrganisationManageWidget'
import ProjectManageWidget from 'components/ProjectManageWidget'

const ProjectsPage: FC = () => {
  useEffect(() => {
    API.trackPage(Constants.pages.PROJECT_SELECT)
  }, [])

  return (
    <div className='app-container container'>
      <div className='py-4'>
        <OrganisationManageWidget />
      </div>

      <PageTitle title={'Projects'}>
        Projects let you create and manage a set of features and configure them
        between multiple app environments.
      </PageTitle>

      <ProjectManageWidget />
    </div>
  )
}

export default ProjectsPage
