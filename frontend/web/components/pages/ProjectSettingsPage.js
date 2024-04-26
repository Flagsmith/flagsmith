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
import Icon from 'components/Icon'
import { getStore } from 'common/store'
import { getRoles } from 'common/services/useRole'
import { getRolesProjectPermissions } from 'common/services/useRolePermission'
import AccountStore from 'common/stores/account-store'
import ImportPage from 'components/import-export/ImportPage'
import FeatureExport from 'components/import-export/FeatureExport'
import ProjectUsage from 'components/ProjectUsage'
import ProjectStore from 'common/stores/project-store'
import Tooltip from 'components/Tooltip'

const ProjectSettingsPage = class extends Component {
  static displayName = 'ProjectSettingsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = { roles: [] }
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
    if (Utils.getFlagsmithHasFeature('show_role_management')) {
      getRoles(
        getStore(),
        { organisation_id: AccountStore.getOrganisation().id },
        { forceRefetch: true },
      ).then((roles) => {
        getRolesProjectPermissions(
          getStore(),
          {
            organisation_id: AccountStore.getOrganisation().id,
            project_id: this.props.match.params.projectId,
            role_id: roles.data.results[0].id,
          },
          { forceRefetch: true },
        ).then((res) => {
          const matchingItems = roles.data.results.filter((item1) =>
            res.data.results.some((item2) => item2.role === item1.id),
          )
          this.setState({ roles: matchingItems })
        })
      })
    }
  }

  onSave = () => {
    toast('Project Saved')
  }

  componentDidUpdate(prevProps) {
    if (this.props.projectId !== prevProps.projectId) {
      AppActions.getProject(this.props.match.params.projectId)
    }
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
      'p-0 modal-sm',
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
    const { name, stale_flags_limit_days } = this.state
    const hasStaleFlagsPermission = Utils.getPlansPermission('STALE_FLAGS')

    return (
      <div className='app-container container'>
        <ProjectProvider
          id={this.props.match.params.projectId}
          onSave={this.onSave}
        >
          {({ deleteProject, editProject, isLoading, isSaving, project }) => {
            if (
              !this.state.stale_flags_limit_days &&
              project?.stale_flags_limit_days
            ) {
              this.state.stale_flags_limit_days = project.stale_flags_limit_days
            }
            if (!this.state.name && project?.name) {
              this.state.name = project.name
            }
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
                editProject(
                  Object.assign({}, project, { name, stale_flags_limit_days }),
                )
            }

            const featureRegexEnabled =
              typeof this.state.feature_name_regex === 'string'

            const hasVersioning =
              Utils.getFlagsmithHasFeature('feature_versioning')
            return (
              <div>
                <PageTitle title={'Project Settings'} />
                {
                  <Tabs urlParam='tab' className='mt-0' uncontrolled>
                    <TabItem tabLabel='General'>
                      <div className='mt-4'>
                        <JSONReference
                          title='Project'
                          json={project}
                          className='mb-3'
                        />
                        <label>Project Name</label>
                        <FormGroup>
                          <form className='col-md-6' onSubmit={saveProject}>
                            <Row className='align-items-start'>
                              <Flex className='ml-0'>
                                <Input
                                  ref={(e) => (this.input = e)}
                                  value={this.state.name}
                                  inputClassName='full-width'
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
                              </Flex>
                            </Row>
                            {!!hasVersioning && (
                              <Tooltip
                                title={
                                  <div>
                                    <label className='mt-4'>
                                      Days before a feature is marked as stale{' '}
                                      <Icon name='info-outlined' />
                                    </label>
                                    <div style={{ width: 80 }} className='ml-0'>
                                      <Input
                                        disabled={!hasStaleFlagsPermission}
                                        ref={(e) => (this.input = e)}
                                        value={
                                          this.state.stale_flags_limit_days
                                        }
                                        onChange={(e) =>
                                          this.setState({
                                            stale_flags_limit_days: parseInt(
                                              Utils.safeParseEventValue(e),
                                            ),
                                          })
                                        }
                                        isValid={!!stale_flags_limit_days}
                                        type='number'
                                        placeholder='Number of Days'
                                      />
                                    </div>
                                  </div>
                                }
                              >
                                {`${
                                  !hasStaleFlagsPermission
                                    ? 'This feature is available with our enterprise plan. '
                                    : ''
                                }If no changes have been made to a feature in any environment within this threshold the feature will be tagged as stale. You will need to enable feature versioning in your environments for stale features to be detected.`}
                              </Tooltip>
                            )}
                            <div className='text-right'>
                              <Button
                                type='submit'
                                id='save-proj-btn'
                                disabled={isSaving || !name}
                                className='ml-3'
                              >
                                {isSaving ? 'Updating' : 'Update'}
                              </Button>
                            </div>
                          </form>
                        </FormGroup>
                      </div>
                      <hr className='py-0 my-4' />
                      <FormGroup className='mt-4 col-md-6'>
                        <Row className='mb-2'>
                          <Switch
                            data-test='js-prevent-flag-defaults'
                            disabled={isSaving}
                            onChange={() =>
                              this.togglePreventDefaults(project, editProject)
                            }
                            checked={project.prevent_flag_defaults}
                          />
                          <h5 className='mb-0 ml-3'>Prevent flag defaults</h5>
                        </Row>
                        <p className='fs-small lh-sm mb-0'>
                          By default, when you create a feature with a value and
                          enabled state it acts as a default for your other
                          environments. Enabling this setting forces the user to
                          create a feature before setting its values per
                          environment.
                        </p>
                      </FormGroup>
                      <FormGroup className='mt-4 col-md-6'>
                        <Row className='mb-2'>
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
                          <h5 className='mb-0 ml-3'>Case sensitive features</h5>
                        </Row>
                        <p className='fs-small lh-sm mb-0'>
                          By default, features are lower case in order to
                          prevent human error. Enabling this will allow you to
                          use upper case characters when creating features.
                        </p>
                      </FormGroup>
                      <FormGroup className='mt-4 col-md-6'>
                        <Row className='mb-2'>
                          <Switch
                            data-test='js-flag-case-sensitivity'
                            disabled={isSaving}
                            onChange={() =>
                              this.toggleFeatureValidation(project, editProject)
                            }
                            checked={featureRegexEnabled}
                          />
                          <h5 className='mb-0 ml-3'>Feature name RegEx</h5>
                        </Row>
                        <p className='fs-small lh-sm mb-0'>
                          This allows you to define a regular expression that
                          all feature names must adhere to.
                        </p>
                        {featureRegexEnabled && (
                          <InputGroup
                            title='Feature Name RegEx'
                            className='mt-4'
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
                                  <Flex>
                                    <Input
                                      ref={(e) => (this.input = e)}
                                      value={this.state.feature_name_regex}
                                      inputClassName='input input--wide'
                                      name='feature-name-regex'
                                      onClick={this.forceSelectionRange}
                                      onKeyUp={this.forceSelectionRange}
                                      showSuccess
                                      onChange={(e) => {
                                        let newRegex =
                                          Utils.safeParseEventValue(e).replace(
                                            '$',
                                            '',
                                          )
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
                                  </Flex>
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
                      {!Utils.getIsEdge() && (
                        <FormGroup className='mt-4 col-md-6'>
                          <Row className='mb-2'>
                            <h5 className='mb-0 mr-3'>
                              Global Edge API Opt in
                            </h5>
                            <Button
                              disabled={isSaving || Utils.isMigrating()}
                              onClick={() =>
                                openConfirm({
                                  body: 'This will migrate your project to the Global Edge API.',
                                  onYes: () => {
                                    this.migrate(project)
                                  },
                                  title: 'Migrate to Global Edge API',
                                })
                              }
                              size='xSmall'
                              theme='outline'
                            >
                              {this.state.migrating || Utils.isMigrating()
                                ? 'Migrating to Edge'
                                : 'Start Migration'}{' '}
                              <Icon
                                name='arrow-right'
                                width={16}
                                fill='#6837FC'
                              />
                            </Button>
                          </Row>
                          <p className='fs-small lh-sm'>
                            Migrate your project onto our Global Edge API.
                            Existing Core API endpoints will continue to work
                            whilst the migration takes place. Find out more{' '}
                            <a
                              href='https://docs.flagsmith.com/advanced-use/edge-api'
                              className='btn-link'
                            >
                              here
                            </a>
                            .
                          </p>
                        </FormGroup>
                      )}
                      <hr className='py-0 my-4' />
                      <FormGroup className='mt-4 col-md-6'>
                        <Row space>
                          <div className='col-md-7'>
                            <h5>Delete Project</h5>
                            <p className='fs-small lh-sm mb-0'>
                              This project will be permanently deleted.
                            </p>
                          </div>
                          <Button
                            onClick={() =>
                              this.confirmRemove(project, () => {
                                this.context.router.history.replace(
                                  '/organisation-settings',
                                )
                                deleteProject(this.props.match.params.projectId)
                              })
                            }
                            className='btn btn-with-icon btn-remove'
                          >
                            <Icon name='trash-2' width={20} fill='#EF4D56' />
                          </Button>
                        </Row>

                        <div className='row'>
                          <div className='col-md-10'></div>
                          <div className='col-md-2 text-right'></div>
                        </div>
                      </FormGroup>
                    </TabItem>
                    <TabItem
                      data-test='js-sdk-settings'
                      tabLabel='SDK Settings'
                    >
                      <div className='mt-4'>
                        <form onSubmit={saveProject}>
                          <FormGroup className='mt-4 col-md-6'>
                            <Row className='mb-2'>
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
                              <h5 className='mb-0 ml-3'>
                                Hide disabled flags from SDKs
                              </h5>
                            </Row>
                            <p className='fs-small lh-sm mb-0'>
                              To prevent letting your users know about your
                              upcoming features and to cut down on payload,
                              enabling this will prevent the API from returning
                              features that are disabled.
                            </p>
                          </FormGroup>
                        </form>
                      </div>
                    </TabItem>
                    <TabItem tabLabel='Usage'>
                      <ProjectUsage
                        projectId={this.props.match.params.projectId}
                      />
                    </TabItem>
                    <TabItem tabLabel='Permissions'>
                      <EditPermissions
                        onSaveUser={() => {
                          this.getPermissions()
                        }}
                        permissions={this.state.permissions}
                        tabClassName='flat-panel'
                        id={this.props.match.params.projectId}
                        level='project'
                        roleTabTitle='Project Permissions'
                        role
                        roles={this.state.roles}
                      />
                    </TabItem>
                    {!!ProjectStore.getEnvs()?.length && (
                      <TabItem data-test='js-import-page' tabLabel='Import'>
                        <ImportPage
                          environmentId={this.props.match.params.environmentId}
                          projectId={this.props.match.params.projectId}
                          projectName={project.name}
                        />
                      </TabItem>
                    )}
                    {!!ProjectStore.getEnvs()?.length &&
                      Utils.getFlagsmithHasFeature(
                        'flagsmith_import_export',
                      ) && (
                        <TabItem tabLabel='Export'>
                          <FeatureExport
                            projectId={this.props.match.params.projectId}
                          />
                        </TabItem>
                      )}
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
