import React, { Component } from 'react';
import Select from 'react-select';

const CreateEnvironmentPage = class extends Component {
    static displayName = 'CreateEnvironmentPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    onSave = (environment) => {
        this.context.router.history.push(`/project/${this.props.match.params.projectId}/environment/${environment.api_key}/features`);
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.CREATE_ENVIRONMENT);

        this.focusTimeout = setTimeout(() => {
            this.input.focus();
            this.focusTimeout = null;
        }, 500);
    };

    componentWillUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }

    render() {
        const { name } = this.state;
        return (
            <div className="app-container container">

                <Permission
                  level="project"
                  permission="CREATE_ENVIRONMENT"
                  id={this.props.match.params.projectId}
                >
                    {({ permission, isLoading }) => (isLoading ? <Loader/> : (
                        <div>
                            {permission ? (
                                <div>
                                    <h3>Create Environment</h3>
                                    <p>
                                        {Constants.strings.ENVIRONMENT_DESCRIPTION}
                                    </p>
                                    <ProjectProvider id={this.props.match.params.projectId} onSave={this.onSave}>
                                        {({ isLoading, isSaving, createEnv, error, project }) => {
                                            if (project && project.environments && project.environments.length && !this.state.selectedEnv) {
                                                this.state.selectedEnv = project.environments[0];
                                            }
                                            return (
                                                <form
                                                  id="create-env-modal"
                                                  onSubmit={(e) => {
                                                      e.preventDefault();
                                                      !isSaving && name && createEnv(name, this.props.match.params.projectId, this.state.selectedEnv && this.state.selectedEnv.api_key);
                                                  }}
                                                >
                                                    <div className="no-pad">
                                                        <div className="row">
                                                            <div className="col-md-12">
                                                                <InputGroup
                                                                  ref={(e) => {
                                                                      if (e) this.input = e;
                                                                  }}
                                                                  inputProps={{ name: 'envName', className: 'full-width' }}
                                                                  onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                                                  isValid={name}
                                                                  type="text" title="Name*"
                                                                  placeholder="An environment name e.g. Develop"
                                                                />
                                                            </div>
                                                            <div className="col-md-6">
                                                                {project && project.environments && project.environments.length && (
                                                                    <InputGroup
                                                                      title="Clone from environment" component={(
                                                                          <Select
                                                                            onChange={(env) => {
                                                                                this.setState({ selectedEnv: project.environments.find(v => v.api_key === env.value) });
                                                                            }}
                                                                            options={project.environments.map(env => ({ label: env.name, value: env.api_key }))}
                                                                            value={this.state.selectedEnv ? {
                                                                                label: this.state.selectedEnv.name,
                                                                                value: this.state.selectedEnv.api_key,
                                                                            } : {
                                                                                label: 'Please select an environment',
                                                                            }}
                                                                          />
                                                                    )}
                                                                    />
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>


                                                    {error && <Error error={error}/>}
                                                    <div className="text-right">
                                                        {permission ? (
                                                            <Button id="create-env-btn" className="mt-3" disabled={isSaving || !name}>
                                                                {isSaving ? 'Creating' : 'Create Environment'}
                                                            </Button>
                                                        ) : (
                                                            <Tooltip
                                                              html
                                                              title={(
                                                                  <Button id="create-env-btn" disabled={isSaving || !name}>
                                                                        Create Environment
                                                                  </Button>
                                                                )}
                                                              place="right"
                                                            >
                                                                {
                                                                    Constants.projectPermissions('Create Environment')
                                                                }
                                                            </Tooltip>
                                                        )}

                                                    </div>
                                                    <p className="text-center faint">
                                                        Not seeing an environment? Check that your project administrator has invited you to it.
                                                    </p>
                                                </form>
                                            );
                                        }}
                                    </ProjectProvider>
                                </div>
                            ) : (
                                <div>
                                    <p className="notification__text ">Check your project permissions</p>

                                    <p>
                                        Although you have been invited to this project, you are not invited to any environments yet!
                                    </p>
                                    <p>
                                        Contact your project administrator asking them to either:
                                        <ul>
                                            <li>
                                                Invite you to an environment (e.g. develop) by visiting <strong>Environment settings</strong>
                                            </li>
                                            <li>
                                                Grant permissions to create an environment under <strong>Project settings</strong>.
                                            </li>
                                        </ul>
                                    </p>
                                </div>
                            )}
                        </div>

                    ))}
                </Permission>
            </div>
        );
    }
};

CreateEnvironmentPage.propTypes = {};

module.exports = ConfigProvider(CreateEnvironmentPage);
