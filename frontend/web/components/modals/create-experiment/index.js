import React, { Component } from 'react'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentityProvider from 'common/providers/IdentityProvider'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import classNames from 'classnames'
import JSONReference from 'components/JSONReference'
import Permission from 'common/providers/Permission'
import {
  setInterceptClose,
  setModalTitle,
} from 'components/modals/base/ModalDefault'
import { getStore } from 'common/store'
import Button from 'components/base/forms/Button'
import { saveFeatureWithValidation } from 'components/saveFeatureWithValidation'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'
import { getChangeRequests } from 'common/services/useChangeRequest'
import ProjectProvider from 'common/providers/ProjectProvider'
import CreateFeature from 'components/modals/create-feature/tabs/CreateFeature'
import FeatureValueTab from 'components/modals/create-feature/tabs/FeatureValue'
import FeatureLimitAlert from 'components/modals/create-feature/FeatureLimitAlert'
import FeatureUpdateSummary from 'components/modals/create-feature/FeatureUpdateSummary'
import FeatureNameInput from 'components/modals/create-feature/FeatureNameInput'
import ExperimentResultsTab from './ExperimentResultsTab'
import moment from 'moment'

const Index = class extends Component {
  static displayName = 'create-experiment'

  constructor(props, context) {
    super(props, context)

    const projectFlagData = this.props.projectFlag
      ? _.cloneDeep(this.props.projectFlag)
      : {
          description: undefined,
          is_archived: undefined,
          is_server_key_only: undefined,
          metadata: [],
          multivariate_options: [],
          name: undefined,
          tags: [],
        }

    const sourceFlag = this.props.identityFlag || this.props.environmentFlag
    const environmentFlagData = sourceFlag ? _.cloneDeep(sourceFlag) : {}

    this.state = {
      changeRequests: [],
      environmentFlag: environmentFlagData,
      featureLimitAlert: { percentage: 0 },
      isEdit: !!this.props.projectFlag,
      projectFlag: projectFlagData,
      scheduledChangeRequests: [],
      valueChanged: false,
    }
  }

  close() {
    closeModal()
  }

  componentDidUpdate(prevProps) {
    ES6Component(this)

    const environmentFlagSource =
      this.props.identityFlag || this.props.environmentFlag
    const prevEnvironmentFlagSource =
      prevProps.identityFlag || prevProps.environmentFlag

    if (
      environmentFlagSource &&
      prevEnvironmentFlagSource &&
      environmentFlagSource.updated_at &&
      prevEnvironmentFlagSource.updated_at &&
      environmentFlagSource.updated_at !== prevEnvironmentFlagSource.updated_at
    ) {
      this.setState({
        environmentFlag: _.cloneDeep(environmentFlagSource),
      })
    }

    if (
      this.props.projectFlag &&
      prevProps.projectFlag &&
      this.props.projectFlag.updated_at &&
      prevProps.projectFlag.updated_at &&
      this.props.projectFlag.updated_at !== prevProps.projectFlag.updated_at
    ) {
      this.setState({
        projectFlag: _.cloneDeep(this.props.projectFlag),
      })
    }

    if (
      !this.props.identity &&
      this.props.environmentVariations !== prevProps.environmentVariations
    ) {
      if (
        this.props.environmentVariations &&
        this.props.environmentVariations.length
      ) {
        this.setState({
          projectFlag: {
            ...this.state.projectFlag,
            multivariate_options:
              this.state.projectFlag.multivariate_options &&
              this.state.projectFlag.multivariate_options.map((v) => {
                const matchingVariation = (
                  this.props.multivariate_options ||
                  this.props.environmentVariations
                ).find((e) => e.multivariate_feature_option === v.id)
                return {
                  ...v,
                  default_percentage_allocation:
                    (matchingVariation &&
                      matchingVariation.percentage_allocation) ||
                    v.default_percentage_allocation ||
                    0,
                }
              }),
          },
        })
      }
    }
  }

  onClosing = () => {
    if (this.state.isEdit) {
      return new Promise((resolve) => {
        if (this.state.valueChanged) {
          openConfirm({
            body: 'Closing this will discard your unsaved changes.',
            noText: 'Cancel',
            onNo: () => resolve(false),
            onYes: () => resolve(true),
            title: 'Discard changes',
            yesText: 'Ok',
          })
        } else {
          resolve(true)
        }
      })
    }
    return Promise.resolve(true)
  }

  componentDidMount = () => {
    setInterceptClose(this.onClosing)
    this.fetchChangeRequests()
    this.fetchScheduledChangeRequests()
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  save = (func, isSaving) => {
    const {
      environmentFlag,
      environmentId,
      identity,
      identityFlag,
      projectFlag: _projectFlag,
      segmentOverrides,
    } = this.props
    const { environmentFlag: stateEnvironmentFlag, projectFlag } = this.state
    const hasMultivariate =
      environmentFlag &&
      environmentFlag.multivariate_feature_state_values &&
      environmentFlag.multivariate_feature_state_values.length
    if (identity) {
      !isSaving &&
        projectFlag.name &&
        func({
          environmentFlag,
          environmentId,
          identity,
          identityFlag: Object.assign({}, identityFlag || {}, {
            enabled: stateEnvironmentFlag.enabled,
            feature_state_value: hasMultivariate
              ? environmentFlag.feature_state_value
              : this.cleanInputValue(stateEnvironmentFlag.feature_state_value),
            multivariate_options:
              stateEnvironmentFlag.multivariate_feature_state_values,
          }),
          projectFlag,
        })
    } else {
      FeatureListStore.isSaving = true
      FeatureListStore.trigger('change')
      !isSaving &&
        projectFlag.name &&
        func(
          this.props.projectId,
          this.props.environmentId,
          {
            default_enabled: stateEnvironmentFlag.enabled,
            description: projectFlag.description,
            initial_value: this.cleanInputValue(
              stateEnvironmentFlag.feature_state_value,
            ),
            is_archived: projectFlag.is_archived,
            is_server_key_only: projectFlag.is_server_key_only,
            metadata:
              !this.props.projectFlag?.metadata ||
              (this.props.projectFlag.metadata !== projectFlag.metadata &&
                projectFlag.metadata.length)
                ? projectFlag.metadata
                : this.props.projectFlag.metadata,
            multivariate_options: projectFlag.multivariate_options,
            name: projectFlag.name,
            tags: projectFlag.tags,
          },
          {
            skipSaveProjectFeature: this.state.skipSaveProjectFeature,
            ..._projectFlag,
          },
          {
            ...environmentFlag,
            multivariate_feature_state_values:
              this.props.environmentVariations ||
              environmentFlag?.multivariate_feature_state_values,
          },
          segmentOverrides,
        )
    }
  }

  parseError = (error) => {
    const { projectFlag } = this.props
    let featureError = error?.message || error?.name?.[0] || error
    let featureWarning = ''
    if (
      featureError?.includes?.('no changes') &&
      projectFlag?.multivariate_options?.length
    ) {
      featureWarning = `Your feature contains no changes to its value, enabled state or environment weights. If you have adjusted any variation values this will have been saved for all environments.`
      featureError = ''
    }
    return { featureError, featureWarning }
  }

  cleanInputValue = (value) => {
    if (value && typeof value === 'string') {
      return value.trim()
    }
    return value
  }

  fetchChangeRequests = (forceRefetch) => {
    const { environmentId, projectFlag } = this.props
    if (!projectFlag?.id) return

    getChangeRequests(
      getStore(),
      {
        committed: false,
        environmentId,
        feature_id: projectFlag?.id,
      },
      { forceRefetch },
    ).then((res) => {
      this.setState({ changeRequests: res.data?.results })
    })
  }

  fetchScheduledChangeRequests = (forceRefetch) => {
    const { environmentId, projectFlag } = this.props
    if (!projectFlag?.id) return

    const date = moment().toISOString()

    getChangeRequests(
      getStore(),
      {
        environmentId,
        feature_id: projectFlag.id,
        live_from_after: date,
      },
      { forceRefetch },
    ).then((res) => {
      this.setState({ scheduledChangeRequests: res.data?.results })
    })
  }

  render() {
    const { environmentFlag, isEdit, projectFlag } = this.state
    const { identity, identityName } = this.props
    const Provider = identity ? IdentityProvider : FeatureListProvider
    const environment = ProjectStore.getEnvironment(this.props.environmentId)
    const isVersioned = !!environment?.use_v2_feature_versioning
    const is4Eyes =
      !!environment &&
      Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)
    const project = ProjectStore.model
    const caseSensitive = project?.only_allow_lower_case_feature_names
    const regex = project?.feature_name_regex
    const controlValue = Utils.calculateControl(
      projectFlag.multivariate_options,
    )
    const invalid =
      !!projectFlag.multivariate_options &&
      projectFlag.multivariate_options.length &&
      controlValue < 0
    const existingChangeRequest = this.props.changeRequest
    const noPermissions = this.props.noPermissions
    let regexValid = true

    try {
      if (!isEdit && projectFlag.name && regex) {
        regexValid = projectFlag.name.match(new RegExp(regex))
      }
    } catch (e) {
      regexValid = false
    }

    return (
      <ProjectProvider id={this.props.projectId}>
        {({ project }) => (
          <Provider
            onSave={() => {
              if (identity) {
                this.close()
              }
              AppActions.refreshFeatures(
                this.props.projectId,
                this.props.environmentId,
              )

              if (is4Eyes && !identity) {
                this.fetchChangeRequests(true)
                this.fetchScheduledChangeRequests(true)
              }

              if (this.props.changeRequest) {
                this.close()
              }
            }}
          >
            {(
              { error, isSaving },
              { createChangeRequest, createFlag, editFeatureValue },
            ) => {
              const saveFeatureValue = saveFeatureWithValidation((schedule) => {
                if ((is4Eyes || schedule) && !identity) {
                  this.setState({ valueChanged: false })
                  const featureStates = [
                    Object.assign({}, this.props.environmentFlag, {
                      enabled: environmentFlag.enabled,
                      feature_state_value: Utils.valueToFeatureState(
                        environmentFlag.feature_state_value,
                      ),
                      multivariate_feature_state_values:
                        environmentFlag.multivariate_feature_state_values,
                    }),
                  ]

                  const getModalTitle = () => {
                    if (schedule) {
                      return 'New Scheduled Flag Update'
                    }
                    if (this.props.changeRequest) {
                      return 'Update Change Request'
                    }
                    return 'New Change Request'
                  }

                  openModal2(
                    getModalTitle(),
                    <ChangeRequestModal
                      showIgnoreConflicts={true}
                      showAssignees={is4Eyes}
                      isScheduledChange={schedule}
                      changeRequest={this.props.changeRequest}
                      projectId={this.props.projectId}
                      environmentId={ProjectStore.getEnvironmentIdFromKey(
                        this.props.environmentId,
                      )}
                      featureId={projectFlag.id}
                      featureStates={featureStates}
                      onSave={({
                        approvals,
                        description,
                        ignore_conflicts,
                        live_from,
                        title,
                      }) => {
                        closeModal2()
                        this.save(
                          (
                            projectId,
                            environmentId,
                            flag,
                            projectFlag,
                            environmentFlag,
                            segmentOverrides,
                          ) => {
                            createChangeRequest(
                              projectId,
                              environmentId,
                              flag,
                              projectFlag,
                              environmentFlag,
                              segmentOverrides,
                              {
                                approvals,
                                description,
                                featureStateId:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.feature_states?.[0]
                                    ?.id,
                                id:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.id,
                                ignore_conflicts,
                                live_from,
                                multivariate_options: flag.multivariate_options,
                                title,
                              },
                              !is4Eyes,
                            )
                          },
                        )
                      }}
                    />,
                  )
                } else {
                  this.setState({ valueChanged: false })
                  this.save(editFeatureValue, isSaving)
                }
              })

              const onCreateFeature = saveFeatureWithValidation(() => {
                this.save(createFlag, isSaving)
              })
              return (
                <Permission
                  level='project'
                  permission='CREATE_FEATURE'
                  id={this.props.projectId}
                >
                  {({ permission: createFeature }) => (
                    <Permission
                      level='project'
                      permission='ADMIN'
                      id={this.props.projectId}
                    >
                      {({ permission: _projectAdmin }) => {
                        this.state.skipSaveProjectFeature = !createFeature

                        return (
                          <div id='create-feature-modal'>
                            {isEdit && !identity ? (
                              <>
                                <Tabs
                                  onChange={() => this.forceUpdate()}
                                  urlParam='tab'
                                  history={this.props.history}
                                  overflowX
                                >
                                  <TabItem
                                    data-test='value'
                                    tabLabelString='Value'
                                    tabLabel={
                                      <Row className='justify-content-center'>
                                        Value{' '}
                                        {this.state.valueChanged && (
                                          <div className='unread ml-2 px-1'>
                                            {'*'}
                                          </div>
                                        )}
                                      </Row>
                                    }
                                  >
                                    <FeatureValueTab
                                      error={error}
                                      createFeature={createFeature}
                                      hideValue={false}
                                      isEdit={isEdit}
                                      noPermissions={noPermissions}
                                      featureState={environmentFlag}
                                      projectFlag={projectFlag}
                                      onEnvironmentFlagChange={(changes) => {
                                        this.setState({
                                          environmentFlag: {
                                            ...this.state.environmentFlag,
                                            ...changes,
                                          },
                                          valueChanged: true,
                                        })
                                      }}
                                      onProjectFlagChange={(changes) => {
                                        this.setState({
                                          projectFlag: {
                                            ...this.state.projectFlag,
                                            ...changes,
                                          },
                                        })
                                      }}
                                      onRemoveMultivariateOption={
                                        this.props.removeMultivariateOption
                                      }
                                    />
                                    <JSONReference
                                      className='mb-3'
                                      showNamesButton
                                      title={'Feature'}
                                      json={projectFlag}
                                    />
                                    <JSONReference
                                      className='mb-3'
                                      title={'Feature state'}
                                      json={this.props.environmentFlag}
                                    />
                                    <FlagValueFooter
                                      is4Eyes={is4Eyes}
                                      isVersioned={isVersioned}
                                      projectId={this.props.projectId}
                                      projectFlag={projectFlag}
                                      environmentId={this.props.environmentId}
                                      environmentName={
                                        _.find(project.environments, {
                                          api_key: this.props.environmentId,
                                        })?.name || ''
                                      }
                                      isSaving={isSaving}
                                      featureName={projectFlag.name}
                                      isInvalid={invalid}
                                      existingChangeRequest={
                                        existingChangeRequest
                                      }
                                      onSaveFeatureValue={saveFeatureValue}
                                    />
                                  </TabItem>
                                  <TabItem
                                    data-test='results'
                                    tabLabelString='Results'
                                    tabLabel={
                                      <Row className='justify-content-center'>
                                        Results
                                      </Row>
                                    }
                                  >
                                    <ExperimentResultsTab
                                      environmentId={this.props.environmentId}
                                      featureName={projectFlag.name}
                                    />
                                  </TabItem>
                                </Tabs>
                              </>
                            ) : (
                              <div
                                className={classNames(
                                  !isEdit ? 'create-feature-tab px-3' : '',
                                )}
                              >
                                <FeatureLimitAlert
                                  projectId={this.props.projectId}
                                  onChange={(featureLimitAlert) =>
                                    this.setState({ featureLimitAlert })
                                  }
                                />
                                <div className={identity ? 'px-3' : ''}>
                                  <FeatureNameInput
                                    value={projectFlag.name}
                                    onChange={(name) =>
                                      this.setState({
                                        projectFlag: {
                                          ...this.state.projectFlag,
                                          name,
                                        },
                                      })
                                    }
                                    caseSensitive={caseSensitive}
                                    regex={regex}
                                    regexValid={regexValid}
                                    autoFocus
                                  />
                                </div>
                                <CreateFeature
                                  projectId={this.props.projectId}
                                  error={error}
                                  featureState={
                                    this.props.environmentFlag ||
                                    environmentFlag
                                  }
                                  projectFlag={projectFlag}
                                  identity={identity}
                                  defaultExperiment={
                                    this.props.defaultExperiment
                                  }
                                  overrideFeatureState={
                                    this.props.identityFlag
                                      ? this.state.environmentFlag
                                      : null
                                  }
                                  onEnvironmentFlagChange={(changes) => {
                                    this.setState({
                                      environmentFlag: {
                                        ...this.state.environmentFlag,
                                        ...changes,
                                      },
                                      valueChanged: true,
                                    })
                                  }}
                                  onProjectFlagChange={(changes) => {
                                    this.setState({
                                      projectFlag: {
                                        ...this.state.projectFlag,
                                        ...changes,
                                      },
                                    })
                                  }}
                                  onRemoveMultivariateOption={
                                    this.props.removeMultivariateOption
                                  }
                                  featureError={
                                    this.parseError(error).featureError
                                  }
                                  featureWarning={
                                    this.parseError(error).featureWarning
                                  }
                                />
                                <FeatureUpdateSummary
                                  identity={identity}
                                  onCreateFeature={onCreateFeature}
                                  isSaving={isSaving}
                                  name={projectFlag.name}
                                  invalid={invalid}
                                  regexValid={regexValid}
                                  featureLimitPercentage={
                                    this.state.featureLimitAlert.percentage
                                  }
                                />
                              </div>
                            )}
                            {identity && (
                              <div className='pr-3'>
                                {identity ? (
                                  <div className='mb-3 mt-4'>
                                    <p className='text-left ml-3 modal-caption fs-small lh-small'>
                                      This will update the feature value for the
                                      user <strong>{identityName}</strong> in
                                      <strong>
                                        {' '}
                                        {
                                          _.find(project.environments, {
                                            api_key: this.props.environmentId,
                                          }).name
                                        }
                                        .
                                      </strong>
                                      {
                                        ' Any segment overrides for this feature will now be ignored.'
                                      }
                                    </p>
                                  </div>
                                ) : (
                                  ''
                                )}

                                <div className='text-right mb-2'>
                                  {identity && (
                                    <div>
                                      <Button
                                        onClick={() => saveFeatureValue()}
                                        data-test='update-feature-btn'
                                        id='update-feature-btn'
                                        disabled={
                                          isSaving ||
                                          !projectFlag.name ||
                                          invalid
                                        }
                                      >
                                        {isSaving
                                          ? 'Updating'
                                          : 'Update Feature'}
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      }}
                    </Permission>
                  )}
                </Permission>
              )
            }}
          </Provider>
        )}
      </ProjectProvider>
    )
  }
}

Index.propTypes = {}

//This will remount the modal when a feature is created
const FeatureProvider = (WrappedComponent) => {
  class HOC extends Component {
    constructor(props) {
      super(props)
      this.state = {
        ...props,
      }
      ES6Component(this)
    }

    componentDidMount() {
      ES6Component(this)
      this.listenTo(
        FeatureListStore,
        'saved',
        ({
          changeRequest,
          createdFlag,
          error,
          isCreate,
          updatedChangeRequest,
        } = {}) => {
          if (error?.data?.metadata) {
            error.data.metadata?.forEach((m) => {
              if (Object.keys(m).length > 0) {
                toast(m.non_field_errors[0], 'danger')
              }
            })
          } else if (error?.data) {
            toast('Error updating the Flag', 'danger')
            return
          } else {
            const isEditingChangeRequest =
              this.props.changeRequest && changeRequest
            const operation = createdFlag || isCreate ? 'Created' : 'Updated'
            const type = changeRequest ? 'Change Request' : 'Feature'

            const toastText = isEditingChangeRequest
              ? `Updated ${type}`
              : `${operation} ${type}`
            const toastAction = changeRequest
              ? {
                  buttonText: 'Open',
                  onClick: () => {
                    closeModal()
                    this.props.history.push(
                      `/project/${this.props.projectId}/environment/${this.props.environmentId}/change-requests/${updatedChangeRequest?.id}`,
                    )
                  },
                }
              : undefined

            toast(toastText, 'success', undefined, toastAction)
          }
          const envFlags = FeatureListStore.getEnvironmentFlags()

          if (createdFlag) {
            const projectFlag = FeatureListStore.getProjectFlags()?.find?.(
              (flag) => flag.name === createdFlag,
            )
            window.history.replaceState(
              {},
              `${document.location.pathname}?feature=${projectFlag.id}`,
            )
            const newEnvironmentFlag = envFlags?.[projectFlag.id] || {}
            setModalTitle(`Edit Feature ${projectFlag.name}`)
            this.setState({
              environmentFlag: {
                ...this.state.environmentFlag,
                ...(newEnvironmentFlag || {}),
              },
              projectFlag,
              valueChanged: false,
            })
          } else if (this.props.projectFlag) {
            const newEnvironmentFlag =
              envFlags?.[this.props.projectFlag.id] || {}
            const newProjectFlag = FeatureListStore.getProjectFlags()?.find?.(
              (flag) => flag.id === this.props.projectFlag.id,
            )
            this.setState({
              environmentFlag: {
                ...this.state.environmentFlag,
                ...(newEnvironmentFlag || {}),
              },
              projectFlag: newProjectFlag,
              valueChanged: false,
            })
          }
        },
      )
    }

    render() {
      return (
        <WrappedComponent
          key={this.state.projectFlag?.id || 'new'}
          {...this.state}
        />
      )
    }
  }
  return HOC
}

const WrappedCreateExperiment = ConfigProvider(Index)

export default FeatureProvider(WrappedCreateExperiment)
