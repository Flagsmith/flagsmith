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
import AccountStore from 'common/stores/account-store'
import ImportPage from 'components/import-export/ImportPage'
import FeatureExport from 'components/import-export/FeatureExport'
import ProjectUsage from 'components/ProjectUsage'
import ProjectStore from 'common/stores/project-store'
import Tooltip from 'components/Tooltip'
import Setting from 'components/Setting'
import PlanBasedBanner from 'components/PlanBasedAccess'
import classNames from 'classnames'
import ProjectProvider from 'common/providers/ProjectProvider'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'
import EditHealthProvider from 'components/EditHealthProvider'
import WarningMessage from 'components/WarningMessage'
import { withRouter } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import SettingTitle from 'components/SettingTitle'
import BetaFlag from 'components/BetaFlag'

const ProjectSettingsPage = class extends Component {
  static displayName = 'ProjectSettingsPage'

  constructor(props) {
    super(props)
    this.projectId = this.props.routeContext.projectId
    this.state = {
      roles: [],
    }
    AppActions.getProject(this.projectId)
    this.getPermissions()
  }

  getPermissions = () => {
    _data
      .get(`${Project.api}projects/${this.projectId}/user-permissions/`)
      .then((permissions) => {
        this.setState({ permissions })
      })
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.PROJECT_SETTINGS)
    getRoles(
      getStore(),
      { organisation_id: AccountStore.getOrganisation().id },
      { forceRefetch: true },
    ).then((roles) => {
      if (!roles?.data?.results?.length) return
      getRoles(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        this.setState({ roles: res.data.results })
      })
    })
  }

  onSave = () => {
    toast('Project Saved')
  }
  componentDidUpdate(prevProps) {
    if (this.props.projectId !== prevProps.projectId) {
      AppActions.getProject(this.projectId)
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

  toggleRealtimeUpdates = (project, editProject) => {
    editProject({
      ...project,
      enable_realtime_updates: !project.enable_realtime_updates,
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
    AppActions.migrateProject(this.projectId)
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
    const { minimum_change_request_approvals, name, stale_flags_limit_days } =
      this.state
    const hasStaleFlagsPermission = Utils.getPlansPermission('STALE_FLAGS')
    const changeRequestsFeature = Utils.getFlagsmithHasFeature(
      'segment_change_requests',
    )
    return (
      <div className='app-container container'>
        <ProjectProvider id={this.projectId} onSave={this.onSave}>
          {({ deleteProject, editProject, isLoading, isSaving, project }) => {
            if (project && this.state.populatedProjectState !== project?.id) {
              this.state.populatedProjectState = project.id
              this.state.stale_flags_limit_days = project.stale_flags_limit_days
              this.state.name = project.name
              this.state.feature_name_regex = project?.feature_name_regex
              this.state.minimum_change_request_approvals =
                project?.minimum_change_request_approvals
            }

            let regexValid = true
            if (this.state.feature_name_regex)
              try {
                new RegExp(this.state.feature_name_regex)
              } catch (e) {
                regexValid = false
              }
            const saveProject = (e) => {
              e?.preventDefault?.()
              const {
                minimum_change_request_approvals,
                name,
                stale_flags_limit_days,
              } = this.state
              !isSaving &&
                name &&
                editProject(
                  Object.assign({}, project, {
                    minimum_change_request_approvals,
                    name,
                    stale_flags_limit_days,
                  }),
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
                      <div className='mt-4 col-md-8'>
                        <JSONReference
                          title='Project'
                          json={project}
                          className='mb-3'
                        />
                        <SettingTitle>Project Information</SettingTitle>
                        <label>Project Name</label>
                        <FormGroup>
                          <form onSubmit={saveProject}>
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
                              <>
                                <div className='d-flex mt-4 gap-2 align-items-center'>
                                  <Tooltip
                                    title={
                                      <>
                                        <label className='mb-0'>
                                          Stale Flag Detection{' '}
                                        </label>
                                        <Icon name='info-outlined' />
                                      </>
                                    }
                                  >
                                    {`If no changes have been made to a feature in any environment within this threshold the feature will be tagged as stale. You will need to enable feature versioning in your environments for stale features to be detected.`}
                                  </Tooltip>
                                  <PlanBasedBanner
                                    feature={'STALE_FLAGS'}
                                    theme={'badge'}
                                  />
                                </div>
                                <div className='d-flex align-items-center gap-2'>
                                  <label
                                    className={classNames('mb-0', {
                                      'opacity-50': !hasStaleFlagsPermission,
                                    })}
                                  >
                                    Mark as stale after
                                  </label>
                                  <div style={{ width: 80 }} className='ml-0'>
                                    <Input
                                      disabled={!hasStaleFlagsPermission}
                                      ref={(e) => (this.input = e)}
                                      value={this.state.stale_flags_limit_days}
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
                                  <label
                                    className={classNames('mb-0', {
                                      'opacity-50': !hasStaleFlagsPermission,
                                    })}
                                  >
                                    Days
                                  </label>
                                </div>
                                {!hasStaleFlagsPermission && (
                                  <PlanBasedBanner
                                    className='mt-2'
                                    feature={'STALE_FLAGS'}
                                    theme={'description'}
                                  />
                                )}
                              </>
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
                        <SettingTitle>Additional Settings</SettingTitle>
                        <FormGroup className='mt-4'>
                          {!!changeRequestsFeature && (
                            <ChangeRequestsSetting
                              feature='4_EYES_PROJECT'
                              value={
                                this.state.minimum_change_request_approvals
                              }
                              onToggle={(v) =>
                                this.setState(
                                  {
                                    minimum_change_request_approvals: v,
                                  },
                                  saveProject,
                                )
                              }
                              onSave={saveProject}
                              onChange={(v) => {
                                this.setState({
                                  minimum_change_request_approvals: v,
                                })
                              }}
                              isLoading={isSaving}
                            />
                          )}
                          <Setting
                            title='Prevent Flag Defaults'
                            data-test='js-prevent-flag-defaults'
                            disabled={isSaving}
                            onChange={() =>
                              this.togglePreventDefaults(project, editProject)
                            }
                            checked={project.prevent_flag_defaults}
                            description={`By default, when you create a feature with a value and
                          enabled state it acts as a default for your other
                          environments. Enabling this setting forces the user to
                          create a feature before setting its values per
                          environment.`}
                          />
                        </FormGroup>
                        <FormGroup className='mt-4'>
                          <Setting
                            data-test='js-flag-case-sensitivity'
                            disabled={isSaving}
                            onChange={() =>
                              this.toggleCaseSensitivity(project, editProject)
                            }
                            checked={
                              !project.only_allow_lower_case_feature_names
                            }
                            title='Case sensitive features'
                            description={`By default, features are lower case in order to
                          prevent human error. Enabling this will allow you to
                          use upper case characters when creating features.`}
                          />
                        </FormGroup>
                        <FormGroup className='mt-4'>
                          <Setting
                            title='Feature name RegEx'
                            data-test='js-flag-case-sensitivity'
                            disabled={isSaving}
                            description={`This allows you to define a regular expression that
                          all feature names must adhere to.`}
                            onChange={() =>
                              this.toggleFeatureValidation(project, editProject)
                            }
                            checked={featureRegexEnabled}
                          />
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
                                            Utils.safeParseEventValue(
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
                                            regex={
                                              this.state.feature_name_regex
                                            }
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
                        {!Utils.getIsEdge() && !!Utils.isSaas() && (
                          <FormGroup className='mt-4'>
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
                                target='_blank'
                                href='https://docs.flagsmith.com/advanced-use/edge-api'
                                className='btn-link'
                                rel='noreferrer'
                              >
                                here
                              </a>
                              .
                            </p>
                          </FormGroup>
                        )}
                        <FormGroup>
                          <SettingTitle danger>Delete Project</SettingTitle>
                          <Row space>
                            <div className=''>
                              <p className='fs-small lh-sm mb-0'>
                                This project will be permanently deleted.
                              </p>
                            </div>
                            <Button
                              onClick={() =>
                                this.confirmRemove(project, () => {
                                  this.props.history.replace(
                                    Utils.getOrganisationHomePage(),
                                  )
                                  deleteProject(this.projectId)
                                })
                              }
                              theme='danger'
                            >
                              Delete Project
                            </Button>
                          </Row>
                        </FormGroup>
                      </div>
                    </TabItem>
                    <TabItem
                      data-test='js-sdk-settings'
                      tabLabel='SDK Settings'
                    >
                      {Utils.isSaas() && (
                        <FormGroup className='mt-4 col-md-8'>
                          <Setting
                            feature='REALTIME'
                            disabled={isSaving}
                            onChange={() =>
                              this.toggleRealtimeUpdates(project, editProject)
                            }
                            checked={project.enable_realtime_updates}
                          />
                        </FormGroup>
                      )}
                      <div className='mt-4'>
                        <form onSubmit={saveProject}>
                          <FormGroup className='mt-4 col-md-8'>
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
                      <ProjectUsage projectId={this.projectId} />
                    </TabItem>
                    {Utils.getFlagsmithHasFeature('feature_health') && (
                      <TabItem
                        data-test='feature-health-settings'
                        tabLabel={
                          <BetaFlag flagName={'feature_health'}>
                            Feature Health
                          </BetaFlag>
                        }
                        tabLabelString='Feature Health'
                      >
                        <EditHealthProvider
                          projectId={this.projectId}
                          tabClassName='flat-panel'
                        />
                      </TabItem>
                    )}
                    <TabItem tabLabel='Permissions'>
                      <EditPermissions
                        onSaveUser={() => {
                          this.getPermissions()
                        }}
                        permissions={this.state.permissions}
                        tabClassName='flat-panel'
                        id={this.projectId}
                        level='project'
                        roleTabTitle='Project Permissions'
                        role
                        roles={this.state.roles}
                      />
                    </TabItem>
                    <TabItem tabLabel='Custom Fields'>
                      <Row space className='mb-2 mt-4'>
                        <Row>
                          <h5>Custom Fields</h5>
                        </Row>
                      </Row>

                      <WarningMessage
                        warningMessage={
                          <span>
                            Custom fields have been moved to{' '}
                            <a
                              href={`/organisation/${
                                AccountStore.getOrganisation()?.id
                              }/settings?tab=custom-fields`}
                              rel='noreferrer'
                            >
                              Organisation Settings
                            </a>
                            .
                          </span>
                        }
                      />
                    </TabItem>
                    {!!ProjectStore.getEnvs()?.length && (
                      <TabItem data-test='js-import-page' tabLabel='Import'>
                        <ImportPage
                          environmentId={this.props.routeContext.environmentId}
                          projectId={this.projectId}
                          projectName={project.name}
                        />
                      </TabItem>
                    )}
                    {!!ProjectStore.getEnvs()?.length && (
                      <TabItem tabLabel='Export'>
                        <FeatureExport projectId={this.projectId} />
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

const ProjectSettingsPageWithContext = (props) => {
  const context = useRouteContext()
  return <ProjectSettingsPage {...props} routeContext={context} />
}

export default withRouter(ConfigProvider(ProjectSettingsPageWithContext))
