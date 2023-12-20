import React, { Component } from 'react'
import IntegrationList from 'components/IntegrationList'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'

const ProjectSettingsPage = class extends Component {
  static displayName = 'ProjectSettingsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }

  render() {
    const integrations = Object.keys(
      JSON.parse(Utils.getFlagsmithValue('integration_data') || '{}'),
    )
    return (
      <div className='app-container container'>
        <PageTitle title={'Integrations'}>
          Enhance Flagsmith with your favourite tools. Have any products you
          want to see us integrate with? Message us and we will be right with
          you.
        </PageTitle>
        <Permission
          level='project'
          permission='CREATE_ENVIRONMENT'
          id={this.props.match.params.projectId}
        >
          {({ isLoading, permission }) =>
            isLoading ? (
              <Loader />
            ) : (
              <div>
                <ProjectProvider
                  id={this.props.projectId}
                  onSave={this.onProjectSave}
                >
                  {({ project }) => (
                    <div>
                      {permission ? (
                        <div>
                          {project && project.environments && (
                            <IntegrationList
                              projectId={this.props.match.params.projectId}
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
}

ProjectSettingsPage.propTypes = {}

module.exports = ProjectSettingsPage
