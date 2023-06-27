import React, { Component } from 'react'
import IntegrationList from 'components/IntegrationList'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'

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
    let integrations = Utils.getFlagsmithValue('integrations') || '[]'
    try {
      integrations = JSON.parse(integrations).sort()
    } catch (e) {
      integrations = []
    }
    return (
      <div className='app-container container'>
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
                <h4>Integrations</h4>
                <p className='text-basic'>
                  Enhance Flagsmith with your favourite tools. Have any products
                  you want to see us integrate with? Message us and we will be
                  right with you.
                </p>

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
