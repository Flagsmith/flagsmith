import React, { Component } from 'react';
import ConfirmRemoveProject from '../modals/ConfirmRemoveProject';
import ConfirmHideFlags from '../modals/ConfirmHideFlags';
import EditPermissions from '../EditPermissions';
import Switch from '../Switch';

const ProjectSettingsPage = class extends Component {
    static displayName = 'ProjectSettingsPage'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
        AppActions.getProject(this.props.match.params.projectId);
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.PROJECT_SETTINGS);
    };

    onSave = () => {
        toast('Project Saved');
    };


    componentWillReceiveProps(newProps) {
        if (newProps.projectId !== this.props.projectId) {
            AppActions.getProject(newProps.match.params.projectId);
        }
    }

    onRemove = () => {
        toast('Your project has been removed');
        this.context.router.history.replace('/projects');
    };

    confirmRemove = (project, cb) => {
        openModal('Remove Project', <ConfirmRemoveProject
          project={project}
          cb={cb}
        />);
    };

    toggleHideDisabledFlags = (project, editProject) => {
        openModal('Hide Disabled Flags', <ConfirmHideFlags
          project={project}
          value={!!project.hide_disabled_flags}
          cb={() => {
              editProject({
                  ...project,
                  hide_disabled_flags: !project.hide_disabled_flags,
              });
          }}
        />);
    };

    render() {
        const { name } = this.state;
        return (
            <div className="app-container container">
                <ProjectProvider id={this.props.match.params.projectId} onRemove={this.onRemove} onSave={this.onSave}>
                    {({ isLoading, isSaving, editProject, deleteProject, project }) => (
                        <div>
                            {(
                                <div className="panel--grey">
                                    <FormGroup>

                                        <form onSubmit={(e) => {
                                            e.preventDefault();
                                            !isSaving && name && editProject(Object.assign({}, project, { name }));
                                        }}
                                        >
                                            <h5>Project Name</h5>
                                            <Row>
                                                <Column className="m-l-0">
                                                    <Input
                                                      ref={e => this.input = e}
                                                      defaultValue={project.name}
                                                      value={this.state.name}
                                                      inputClassName="input input--wide"
                                                      name="proj-name"
                                                      onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                                      isValid={name && name.length}
                                                      type="text" title={<h3>Project Name</h3>}
                                                      placeholder="My Project Name"
                                                    />
                                                </Column>
                                                <Button id="save-proj-btn" disabled={isSaving || !name}>
                                                    {isSaving ? 'Updating' : 'Update Name'}
                                                </Button>
                                            </Row>
                                        </form>
                                    </FormGroup>
                                </div>
                            )}
                            <EditPermissions tabClassName="flat-panel" id={this.props.match.params.projectId} level="project"/>

                            <FormGroup className="mt-4">
                                <h3>Hide disabled flags from SDKs</h3>
                                <div className="row">
                                    <div className="col-md-10">
                                        <p>
                                              To prevent letting your users know about your upcoming features and to cut down on payload, enabling this will prevent the API from returning features that are disabled.
                                        </p>
                                    </div>
                                    <div className="col-md-2 text-right">
                                        <Switch disabled={isSaving} onChange={() => this.toggleHideDisabledFlags(project, editProject)} checked={project.hide_disabled_flags}/>
                                    </div>
                                </div>
                            </FormGroup>

                            <FormGroup className="mt-4">
                                <h3>Delete Project</h3>
                                <div className="row">
                                    <div className="col-md-10">
                                        <p>
                                        This project will be permanently deleted.
                                        </p>
                                    </div>
                                    <div className="col-md-2 text-right">
                                    <Button
                                      onClick={() => this.confirmRemove(project, () => {
                                          deleteProject(this.props.match.params.projectId);
                                      })}
                                      className="btn btn--with-icon ml-auto btn--remove"
                                    >
                                        <RemoveIcon/>
                                    </Button>
                                    </div>
                                </div>
                            </FormGroup>
                        </div>
                    )}
                </ProjectProvider>
            </div>
        );
    }
};

ProjectSettingsPage.propTypes = {};

module.exports = ConfigProvider(ProjectSettingsPage);
