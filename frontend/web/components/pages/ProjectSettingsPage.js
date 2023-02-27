import React, { Component } from 'react';
import ConfirmRemoveProject from '../modals/ConfirmRemoveProject';
import ConfirmHideFlags from '../modals/ConfirmHideFlags';
import EditPermissions from '../EditPermissions';
import Switch from '../Switch';
import _data from '../../../common/data/base/_data';
import Tabs from '../base/forms/Tabs'
import TabItem from '../base/forms/TabItem'
import RegexTester from "../RegexTester";
import ConfigProvider from 'common/providers/ConfigProvider';
import Constants from 'common/constants';

const ProjectSettingsPage = class extends Component {
    static displayName = 'ProjectSettingsPage'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
        AppActions.getProject(this.props.match.params.projectId);
        this.getPermissions();
    }

    getPermissions = () => {
        _data.get(`${Project.api}projects/${this.props.match.params.projectId}/user-permissions/`)
            .then((permissions) => {
                this.setState({ permissions });
            });
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

    togglePreventDefaults = (project, editProject) => {
        editProject({
            ...project,
            prevent_flag_defaults: !project.prevent_flag_defaults,
        });
    };

    toggleFeatureValidation = (project, editProject) => {
        if (this.state.feature_name_regex) {
            editProject({
                ...project,
                feature_name_regex: null,
            });
            this.setState({feature_name_regex: null})
        } else {
            this.setState({feature_name_regex:"^.+$"})
        }
    };

    updateFeatureNameRegex = (project, editProject) => {
        editProject({
            ...project,
            feature_name_regex: this.state.feature_name_regex,
        });
    };

    toggleCaseSensitivity = (project, editProject) => {
        editProject({
            ...project,
            only_allow_lower_case_feature_names: !project.only_allow_lower_case_feature_names,
        });
    };

    migrate = () => {
        AppActions.migrateProject(this.props.match.params.projectId);
    }

    forceSelectionRange = (e)=>{
        const input = e.currentTarget;
        setTimeout(()=>{
            const range = input.selectionStart;
            if (range === input.value.length) {
                input.setSelectionRange(input.value.length-1,input.value.length-1)
            }
        },0)
    }

    render() {
        const { name } = this.state;

        return (
            <div className="app-container container">
                <ProjectProvider id={this.props.match.params.projectId} onRemove={this.onRemove} onSave={this.onSave}>
                    {({ isLoading, isSaving, editProject, deleteProject, project }) => {
                        if(!this.state.populatedProjectState && project?.feature_name_regex) {
                            this.state.populatedProjectState = true
                            this.state.feature_name_regex = project?.feature_name_regex
                        }
                        let regexValid = true;
                        if(this.state.feature_name_regex)
                        try {
                            new RegExp(this.state.feature_name_regex);
                        } catch(e) {
                            regexValid = false;
                        }
                        const featureRegexEnabled = typeof this.state.feature_name_regex === 'string';
                        return (
                            <div>
                                {(
                                    <Tabs inline transparent uncontrolled>
                                        <TabItem tabLabel="General" tabIcon="ion-md-settings">
                                            <div className="mt-4">
                                                <h3>Project Name</h3>
                                                <FormGroup>
                                                    <form onSubmit={(e) => {
                                                        e.preventDefault();
                                                        !isSaving && name && editProject(Object.assign({}, project, { name }));
                                                    }}
                                                    >
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

                                            <FormGroup className="mt-4">
                                                <h3>Hide disabled flags from SDKs</h3>
                                                <div className="row">
                                                    <div className="col-md-10">
                                                        <p>
                                                            To prevent letting your users know about your upcoming features
                                                            and to cut down on payload, enabling this will prevent the API
                                                            from returning features that are disabled.
                                                        </p>
                                                    </div>
                                                    <div className="col-md-2 text-right">
                                                        <Switch
                                                            data-test="js-hide-disabled-flags" disabled={isSaving}
                                                            onChange={() => this.toggleHideDisabledFlags(project, editProject)}
                                                            checked={project.hide_disabled_flags}
                                                        />
                                                    </div>
                                                </div>
                                            </FormGroup>
                                            <FormGroup className="mt-4">
                                                <h3>Prevent flag defaults</h3>
                                                <div className="row">
                                                    <div className="col-md-10">
                                                        <p>
                                                            By default, when you create a feature with a value and enabled
                                                            state it acts as a default for your other environments. Enabling
                                                            this setting forces the user to create a feature before setting
                                                            its values per environment.
                                                        </p>
                                                    </div>
                                                    <div className="col-md-2 text-right">
                                                        <Switch
                                                            data-test="js-hide-disabled-flags" disabled={isSaving}
                                                            onChange={() => this.togglePreventDefaults(project, editProject)}
                                                            checked={project.prevent_flag_defaults}
                                                        />
                                                    </div>
                                                </div>
                                            </FormGroup>
                                            {
                                                Utils.getFlagsmithHasFeature("case_sensitive_flags") && (
                                                    <FormGroup className="mt-4">
                                                        <h3>Case sensitive features</h3>
                                                        <div className="row">
                                                            <div className="col-md-10">
                                                                <p>
                                                                    By default, features are lower case in order to prevent human error. Enabling this will allow you to use upper case characters when creating features.
                                                                </p>
                                                            </div>
                                                            <div className="col-md-2 text-right">
                                                                <Switch
                                                                    data-test="js-flag-case-sensitivity" disabled={isSaving} onChange={() => this.toggleCaseSensitivity(project, editProject)}
                                                                    checked={!project.only_allow_lower_case_feature_names}
                                                                />
                                                            </div>
                                                        </div>
                                                    </FormGroup>
                                                )
                                            }
                                            {
                                                Utils.getFlagsmithHasFeature("feature_name_regex") && (
                                                    <FormGroup className="mt-4">
                                                        <h3>Feature name RegEx</h3>
                                                        <div className="row">
                                                            <div className="col-md-10">
                                                                <p>
                                                                    This allows you to define a regular expression that all
                                                                    feature names must adhere to.
                                                                </p>
                                                            </div>
                                                            <div className="col-md-2 text-right">
                                                                <Switch
                                                                    data-test="js-flag-case-sensitivity" disabled={isSaving}
                                                                    onChange={() => this.toggleFeatureValidation(project, editProject)}
                                                                    checked={featureRegexEnabled}
                                                                />
                                                            </div>
                                                        </div>
                                                        {featureRegexEnabled && (
                                                            <InputGroup title="Feature Name RegEx"
                                                                        component={(
                                                                            <form onSubmit={(e)=>{
                                                                                e.preventDefault()
                                                                                if(regexValid) {
                                                                                    this.updateFeatureNameRegex(project, editProject);
                                                                                }
                                                                            }}>
                                                                                <Row>
                                                                                    <Input
                                                                                        ref={e => this.input = e}
                                                                                        value={this.state.feature_name_regex}
                                                                                        inputClassName="input input--wide"
                                                                                        name="feature-name-regex"
                                                                                        onClick={this.forceSelectionRange}
                                                                                        onKeyUp={this.forceSelectionRange}
                                                                                        showSuccess
                                                                                        onChange={e => {
                                                                                            let newRegex = Utils.safeParseEventValue(e).replace("$","");
                                                                                            if (!newRegex.startsWith("^")) {
                                                                                                newRegex = `^${newRegex}`
                                                                                            }
                                                                                            if (!newRegex.endsWith("$")) {
                                                                                                newRegex = `${newRegex}$`
                                                                                            }
                                                                                            this.setState({feature_name_regex:newRegex})
                                                                                        }}
                                                                                        isValid={regexValid}
                                                                                        type="text"
                                                                                        placeholder="Regular Expression"
                                                                                    />
                                                                                    <Button className="ml-2" disabled={!regexValid||isLoading}>
                                                                                        Save
                                                                                    </Button>
                                                                                    <ButtonLink type="button" onClick={()=>{
                                                                                        openModal(<span>RegEx Tester</span>, (
                                                                                            <RegexTester regex={this.state.feature_name_regex} onChange={(feature_name_regex)=>this.setState({feature_name_regex})}/>
                                                                                        ))
                                                                                    }} className="ml-2" disabled={!regexValid||isLoading}>
                                                                                        Test RegEx
                                                                                    </ButtonLink>
                                                                                </Row>
                                                                            </form>
                                                                        )}
                                                            />
                                                        )}
                                                    </FormGroup>
                                                )
                                            }
                                            {!Utils.getIsEdge() && this.props.hasFeature('edge_identities') && (
                                                <FormGroup className="mt-4">
                                                    <h3>Global Edge API Opt in</h3>
                                                    <div className="row">
                                                        <div className="col-md-10">
                                                            <p>
                                                                Migrate your project onto our Global Edge API. Existing Core
                                                                API endpoints will continue to work whilst the migration
                                                                takes place. Find out more <a
                                                                href="https://docs.flagsmith.com/advanced-use/edge-api"
                                                            >here</a>.
                                                            </p>
                                                        </div>
                                                        <div className="col-md-2 text-right">
                                                            <Button
                                                                disabled={isSaving || Utils.isMigrating()}
                                                                onClick={() => openConfirm('Are you sure?', 'This will migrate your project to the Global Edge API.', () => {
                                                                    this.migrate(project);
                                                                })}
                                                            >
                                                                {this.state.migrating || Utils.isMigrating() ? 'Migrating to Edge' : 'Start Migration'}
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </FormGroup>
                                            )}

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
                                        </TabItem>
                                        <TabItem tabLabel="Members" tabIcon="ion-md-people">
                                            <EditPermissions
                                                onSaveUser={() => {
                                                    this.getPermissions();
                                                }}
                                                permissions={this.state.permissions}
                                                tabClassName="flat-panel"
                                                id={this.props.match.params.projectId}
                                                level="project"
                                            />
                                        </TabItem>
                                    </Tabs>
                                )}
                            </div>
                        )
                    }}
                </ProjectProvider>
            </div>
        );
    }
};

ProjectSettingsPage.propTypes = {};

module.exports = ConfigProvider(ProjectSettingsPage);
