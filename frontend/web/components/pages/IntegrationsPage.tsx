import React, { FC, useEffect } from 'react'
import IntegrationList from 'components/IntegrationList'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import InfoMessage from 'components/InfoMessage'
import { Link } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import AccountStore from 'common/stores/account-store'
import ProjectProvider from 'common/providers/ProjectProvider'
import API from 'project/api'
type ProjectSettingsPageType = {
  match: {
    params: {
      projectId: string
    }
  }
}
const ProjectSettingsPage: FC<ProjectSettingsPageType> = ({ match }) => {
  useEffect(() => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }, [])

  const integrations = Object.keys(Utils.getIntegrationData())

  return (
    <div className='app-container container'>
      <PageTitle title={'Integrations'}>
        Enhance Flagsmith with your favourite tools. Have any products you want
        to see us integrate with? Message us and we will be right with you.
      </PageTitle>
      {Utils.getFlagsmithHasFeature('organisation_integrations') && (
        <InfoMessage collapseId='project-integrations'>
          You can also set{' '}
          <Link
            to={`/organisation/${
              AccountStore.getOrganisation()?.id
            }/integrations`}
          >
            Organisation Integrations
          </Link>
          . If you add any of the same integrations here, they will override the
          ones set at the organization level.
        </InfoMessage>
      )}

      <Permission
        level='project'
        permission='CREATE_ENVIRONMENT'
        id={match.params.projectId}
      >
        {({ isLoading, permission }) =>
          isLoading ? (
            <Loader />
          ) : (
            <div>
              <ProjectProvider id={match.params.projectId}>
                {({ project }: { project: Project }) => (
                  <div>
                    {permission ? (
                      <div>
                        {project && project.environments && (
                          <IntegrationList
                            projectId={match.params.projectId}
                            integrations={integrations}
                          />
                        )}
                      </div>
                    ) : (
                      <div>{Constants.projectPermissions('Admin')}</div>
                    )}
                  </div>
                )}
              </ProjectProvider>
            </div>
          )
        }
      </Permission>
    </div>
  )
}

export default ProjectSettingsPage
