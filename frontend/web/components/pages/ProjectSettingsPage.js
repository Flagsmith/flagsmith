import React, { Component } from 'react'
import ConfirmRemoveProject from 'components/modals/ConfirmRemoveProject'
import ConfirmHideFlags from 'components/modals/ConfirmHideFlags'
import EditPermissions from 'components/EditPermissions'
import Switch from 'components/Switch'
import _data from 'common/data/base/_data'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import RegexTester from 'components/RegexTester'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import JSONReference from 'components/JSONReference'
import PageTitle from 'components/PageTitle'
const ProjectSettingsPage = class extends Component {
  static displayName = 'ProjectSettingsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {}
    AppActions.getProject(this.props.match.params.projectId)
    this.getPermissions()
  }

  getPermissions = () => {
    _data
      .get(
        `${Project.api}projects/${this.props.match.params.projectId}/user-permissions/`,
      )
      .then((permissions) => {
        this.setState({ permissions })
      })
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.PROJECT_SETTINGS)
  }

  onSave = () => {
    toast('Project Saved')
  }

  componentDidUpdate(prevProps) {
    if (this.props.projectId !== prevProps.projectId) {
      AppActions.getProject(this.props.match.params.projectId)
    }
  }

  onRemove = () => {
    toast('Your project has been removed')
    this.context.router.history.replace('/projects')
  }

  confirmRemove = (project, cb) => {
    openModal(
      'Delete Project',
      <ConfirmRemoveProject project={project} cb={cb} />,
      'p-0',
    )
  }

  toggleHideDisabledFlags = (project, editProject) => {
    openModal(
      'Hide Disabled Flags',
      <ConfirmHideFlags
        project={project}
        value={!!project.hide_disabled_flags}
        cb={() => {
          editProject({
            ...project,
            hide_disabled_flags: !project.hide_disabled_flags,
          })
        }}
      />,
      'p-0',
    )
  }

  togglePreventDefaults = (project, editProject) => {
    editProject({
      ...project,
      prevent_flag_defaults: !project.prevent_flag_defaults,
    })
  }

  toggleFeatureValidation = (project, editProject) => {
    if (this.state.feature_name_regex) {
      editProject({
        ...project,
        feature_name_regex: null,
      })
      this.setState({ feature_name_regex: null })
    } else {
      this.setState({ feature_name_regex: '^.+$' })
    }
  }

  updateFeatureNameRegex = (project, editProject) => {
    editProject({
      ...project,
      feature_name_regex: this.state.feature_name_regex,
    })
  }

  toggleCaseSensitivity = (project, editProject) => {
    editProject({
      ...project,
      only_allow_lower_case_feature_names:
        !project.only_allow_lower_case_feature_names,
    })
  }

  migrate = () => {
    AppActions.migrateProject(this.props.match.params.projectId)
  }

  forceSelectionRange = (e) => {
    const input = e.currentTarget
    setTimeout(() => {
      const range = input.selectionStart
      if (range === input.value.length) {
        input.setSelectionRange(input.value.length - 1, input.value.length - 1)
      }
    }, 0)
  }

  render() {
    const { name } = this.state

    return (
      <div className='app-container container'>
        <ProjectProvider
          id={this.props.match.params.projectId}
          onRemove={this.onRemove}
          onSave={this.onSave}
        >
          {({ deleteProject, editProject, isLoading, isSaving, project }) => {
            if (
              !this.state.populatedProjectState &&
              project?.feature_name_regex
            ) {
              this.state.populatedProjectState = true
              this.state.feature_name_regex = project?.feature_name_regex
            }
            let regexValid = true
            if (this.state.feature_name_regex)
              try {
                new RegExp(this.state.feature_name_regex)
              } catch (e) {
                regexValid = false
              }
            const saveProject = (e) => {
              e.preventDefault()
              !isSaving &&
                name &&
                editProject(Object.assign({}, project, { name }))
            }

            const featureRegexEnabled =
              typeof this.state.feature_name_regex === 'string'
            return (
              <div>
                <PageTitle title={'Project Settings'} />
                {
                  <Tabs className='mt-0' uncontrolled>
                    <TabItem tabLabel='General'>
                      <div className='mt-4'>
                        <JSONReference title='Project' json={project} />
                        <label>Project Name</label>
                        <FormGroup>
                          <form onSubmit={saveProject}>
                            <Row className='align-items-start'>
                              <Column className='ml-0'>
                                <Input
                                  ref={(e) => (this.input = e)}
                                  defaultValue={project.name}
                                  value={this.state.name}
                                  inputClassName='input--wide'
                                  name='proj-name'
                                  onChange={(e) =>
                                    this.setState({
                                      name: Utils.safeParseEventValue(e),
                                    })
                                  }
                                  isValid={name && name.length}
                                  type='text'
                                  title={<label>Project Name</label>}
                                  placeholder='My Project Name'
                                />
                              </Column>
                              <Button
                                type='submit'
                                id='save-proj-btn'
                                disabled={isSaving || !name}
                              >
                                {isSaving ? 'Updating' : 'Update Name'}
                              </Button>
                            </Row>
                          </form>
                        </FormGroup>
                      </div>

                      <FormGroup className='mt-4'>
                        <h5>Prevent flag defaults</h5>
                        <div className='row'>
                          <div className='col-md-10'>
                            <p className='fs-small lh-sm'>
                              By default, when you create a feature with a value
                              and enabled state it acts as a default for your
                              other environments. Enabling this setting forces
                              the user to create a feature before setting its
                              values per environment.
                            </p>
                          </div>
                          <div className='col-md-2 text-right'>
                            <Switch
                              data-test='js-prevent-flag-defaults'
                              disabled={isSaving}
                              onChange={() =>
                                this.togglePreventDefaults(project, editProject)
                              }
                              checked={project.prevent_flag_defaults}
                            />
                          </div>
                        </div>
                      </FormGroup>
                      <FormGroup className='mt-4'>
                        <h5>Case sensitive features</h5>
                        <div className='row'>
                          <div className='col-md-10'>
                            <p className='fs-small lh-sm'>
                              By default, features are lower case in order to
                              prevent human error. Enabling this will allow you
                              to use upper case characters when creating
                              features.
                            </p>
                          </div>
                          <div className='col-md-2 text-right'>
                            <Switch
                              data-test='js-flag-case-sensitivity'
                              disabled={isSaving}
                              onChange={() =>
                                this.toggleCaseSensitivity(project, editProject)
                              }
                              checked={
                                !project.only_allow_lower_case_feature_names
                              }
                            />
                          </div>
                        </div>
                      </FormGroup>
                      <FormGroup className='mt-4'>
                        <h5>Feature name RegEx</h5>
                        <div className='row'>
                          <div className='col-md-10'>
                            <p className='fs-small lh-sm'>
                              This allows you to define a regular expression
                              that all feature names must adhere to.
                            </p>
                          </div>
                          <div className='col-md-2 text-right'>
                            <Switch
                              data-test='js-flag-case-sensitivity'
                              disabled={isSaving}
                              onChange={() =>
                                this.toggleFeatureValidation(
                                  project,
                                  editProject,
                                )
                              }
                              checked={featureRegexEnabled}
                            />
                          </div>
                        </div>
                        {featureRegexEnabled && (
                          <InputGroup
                            title='Feature Name RegEx'
                            component={
                              <form
                                onSubmit={(e) => {
                                  e.preventDefault()
                                  if (regexValid) {
                                    this.updateFeatureNameRegex(
                                      project,
                                      editProject,
                                    )
                                  }
                                }}
                              >
                                <Row>
                                  <Input
                                    ref={(e) => (this.input = e)}
                                    value={this.state.feature_name_regex}
                                    inputClassName='input input--wide'
                                    name='feature-name-regex'
                                    onClick={this.forceSelectionRange}
                                    onKeyUp={this.forceSelectionRange}
                                    showSuccess
                                    onChange={(e) => {
                                      let newRegex = Utils.safeParseEventValue(
                                        e,
                                      ).replace('$', '')
                                      if (!newRegex.startsWith('^')) {
                                        newRegex = `^${newRegex}`
                                      }
                                      if (!newRegex.endsWith('$')) {
                                        newRegex = `${newRegex}$`
                                      }
                                      this.setState({
                                        feature_name_regex: newRegex,
                                      })
                                    }}
                                    isValid={regexValid}
                                    type='text'
                                    placeholder='Regular Expression'
                                  />
                                  <Button
                                    className='ml-2'
                                    type='submit'
                                    disabled={!regexValid || isLoading}
                                  >
                                    Save
                                  </Button>
                                  <Button
                                    theme='text'
                                    type='button'
                                    onClick={() => {
                                      openModal(
                                        <span>RegEx Tester</span>,
                                        <RegexTester
                                          regex={this.state.feature_name_regex}
                                          onChange={(feature_name_regex) =>
                                            this.setState({
                                              feature_name_regex,
                                            })
                                          }
                                        />,
                                      )
                                    }}
                                    className='ml-2'
                                    disabled={!regexValid || isLoading}
                                  >
                                    Test RegEx
                                  </Button>
                                </Row>
                              </form>
                            }
                          />
                        )}
                      </FormGroup>
                      {!Utils.getIsEdge() &&
                        this.props.hasFeature('edge_identities') && (
                          <FormGroup className='mt-4'>
                            <h5>Global Edge API Opt in</h5>
                            <div className='row'>
                              <div className='col-md-10'>
                                <p className='fs-small lh-sm'>
                                  Migrate your project onto our Global Edge API.
                                  Existing Core API endpoints will continue to
                                  work whilst the migration takes place. Find
                                  out more{' '}
                                  <a href='https://docs.flagsmith.com/advanced-use/edge-api'>
                                    here
                                  </a>
                                  .
                                </p>
                              </div>
                              <div className='col-md-2 text-right'>
                                <Button
                                  disabled={isSaving || Utils.isMigrating()}
                                  onClick={() =>
                                    openConfirm(
                                      'Are you sure?',
                                      'This will migrate your project to the Global Edge API.',
                                      () => {
                                        this.migrate(project)
                                      },
                                    )
                                  }
                                >
                                  {this.state.migrating || Utils.isMigrating()
                                    ? 'Migrating to Edge'
                                    : 'Start Migration'}
                                </Button>
                              </div>
                            </div>
                          </FormGroup>
                        )}
                      <FormGroup className='mt-4'>
                        <h5>Delete Project</h5>
                        <div className='row'>
                          <div className='col-md-10'>
                            <p className='fs-small lh-sm'>
                              This project will be permanently deleted.
                            </p>
                          </div>
                          <div className='col-md-2 text-right'>
                            <Button
                              onClick={() =>
                                this.confirmRemove(project, () => {
                                  deleteProject(
                                    this.props.match.params.projectId,
                                  )
                                })
                              }
                              className='btn btn--with-icon ml-auto btn--remove'
                            >
                              <RemoveIcon />
                            </Button>
                          </div>
                        </div>
                      </FormGroup>
                    </TabItem>
                    <TabItem
                      data-test='js-sdk-settings'
                      tabLabel='SDK Settings'
                    >
                      <div className='mt-4'>
                        <form onSubmit={saveProject}>
                          <FormGroup className='mt-4'>
                            <h5>Hide disabled flags from SDKs</h5>
                            <div className='row'>
                              <div className='col-md-10'>
                                <p className='fs-small lh-sm'>
                                  To prevent letting your users know about your
                                  upcoming features and to cut down on payload,
                                  enabling this will prevent the API from
                                  returning features that are disabled.
                                </p>
                              </div>
                              <div className='col-md-2 text-right'>
                                <Switch
                                  data-test='js-hide-disabled-flags'
                                  disabled={isSaving}
                                  onChange={() =>
                                    this.toggleHideDisabledFlags(
                                      project,
                                      editProject,
                                    )
                                  }
                                  checked={project.hide_disabled_flags}
                                />
                              </div>
                            </div>
                          </FormGroup>
                        </form>
                      </div>
                    </TabItem>
                    <TabItem tabLabel='Members'>
                      <EditPermissions
                        onSaveUser={() => {
                          this.getPermissions()
                        }}
                        permissions={this.state.permissions}
                        tabClassName='flat-panel'
                        id={this.props.match.params.projectId}
                        level='project'
                      />
                    </TabItem>
                  </Tabs>
                }
              </div>
            )
          }}
        </ProjectProvider>
      </div>
    )
  }
}

ProjectSettingsPage.propTypes = {}

module.exports = ConfigProvider(ProjectSettingsPage)
