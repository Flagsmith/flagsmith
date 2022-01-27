import React, { Component } from 'react';
import IntegrationList from '../IntegrationList';


const ProjectSettingsPage = class extends Component {
    static displayName = 'ProjectSettingsPage'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.INTEGRATIONS);
    };

    render() {
        let integrations = this.props.getValue('integrations') || '[]';
        try {
            integrations = JSON.parse(integrations).sort();
        } catch (e) {
            integrations = [];
        }
        return (
            <div className="app-container container">
                <Permission
                  level="project"
                  permission="CREATE_ENVIRONMENT"
                  id={this.props.match.params.projectId}
                >
                    {({ permission, isLoading }) => (isLoading ? <Loader/> : (
                        <div>
                            <h3>
                                Integrations
                            </h3>
                            <p>
                                Enhance Flagsmith with your favourite tools. Have any products you want to see us integrate with? Message us and we will be right with you.
                            </p>

                            <ProjectProvider id={this.props.projectId} onSave={this.onProjectSave}>
                                {({ isLoading, project }) => (
                                    <div>
                                        {permission ? (
                                            <div>
                                                {project && project.environments && (
                                                <IntegrationList projectId={this.props.match.params.projectId} integrations={integrations}/>
                                                )}
                                            </div>
                                        ) : (
                                            <div>
                                                { Constants.projectPermissions('Admin') }
                                            </div>
                                        )}
                                    </div>
                                )}
                            </ProjectProvider>
                        </div>
                    ))}
                </Permission>
            </div>
        );
    }
};

ProjectSettingsPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(ProjectSettingsPage));
