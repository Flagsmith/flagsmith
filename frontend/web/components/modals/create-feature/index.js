import React, { Component } from 'react'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import moment from 'moment'
import Constants from 'common/constants'
import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentityProvider from 'common/providers/IdentityProvider'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import SegmentOverrides from 'components/SegmentOverrides'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import classNames from 'classnames'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import ErrorMessage from 'components/ErrorMessage'
import Permission from 'common/providers/Permission'
import IdentitySelect from 'components/IdentitySelect'
import {
  setInterceptClose,
  setModalTitle,
} from 'components/modals/base/ModalDefault'
import Icon from 'components/Icon'
import ModalHR from 'components/modals/ModalHR'
import FeatureValue from 'components/feature-summary/FeatureValue'
import { getStore } from 'common/store'
import Button from 'components/base/forms/Button'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import { getGithubIntegration } from 'common/services/useGithubIntegration'
import { removeUserOverride } from 'components/RemoveUserOverride'
import ExternalResourcesLinkTab from 'components/ExternalResourcesLinkTab'
import { saveFeatureWithValidation } from 'components/saveFeatureWithValidation'
import FeatureHistory from 'components/FeatureHistory'
import WarningMessage from 'components/WarningMessage'
import FeatureAnalytics from 'components/feature-page/FeatureNavTab/FeatureAnalytics'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'
import { getPermission } from 'common/services/usePermission'
import { getChangeRequests } from 'common/services/useChangeRequest'
import FeatureHealthTabContent from 'components/feature-health/FeatureHealthTabContent'
import { IonIcon } from '@ionic/react'
import { warning } from 'ionicons/icons'
import FeaturePipelineStatus from 'components/release-pipelines/FeaturePipelineStatus'
import FeatureInPipelineGuard from 'components/release-pipelines/FeatureInPipelineGuard'
import FeatureCodeReferencesContainer from 'components/feature-page/FeatureNavTab/CodeReferences/FeatureCodeReferencesContainer'
import BetaFlag from 'components/BetaFlag'
import ProjectProvider from 'common/providers/ProjectProvider'
import CreateFeature from './tabs/CreateFeature'
import FeatureSettings from './tabs/FeatureSettings'
import FeatureValueTab from './tabs/FeatureValue'
import FeatureLimitAlert from './FeatureLimitAlert'
import FeatureUpdateSummary from './FeatureUpdateSummary'
import FeatureNameInput from './FeatureNameInput'

const Index = class extends Component {
  static displayName = 'create-feature'

  constructor(props, context) {
    super(props, context)
    if (this.props.projectFlag) {
      this.userOverridesPage(1, true)
    }

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
      enabledIndentity: false,
      enabledSegment: false,
      environmentFlag: environmentFlagData,
      externalResource: {},
      externalResources: [],
      featureContentType: {},
      featureLimitAlert: { percentage: 0 },
      githubId: '',
      hasIntegrationWithGithub: false,
      hasMetadataRequired: false,
      isEdit: !!this.props.projectFlag,
      period: 30,
      projectFlag: projectFlagData,
      scheduledChangeRequests: [],
      segmentsChanged: false,
      selectedIdentity: null,
      settingsChanged: false,
      userOverridesError: false,
      userOverridesNoPermission: false,
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
        const projectFlagChanged = this.state.settingsChanged
        const environmentFlagChanged = this.state.valueChanged
        const segmentOverridesChanged = this.state.segmentsChanged
        if (
          projectFlagChanged ||
          environmentFlagChanged ||
          segmentOverridesChanged
        ) {
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
    if (Utils.getPlansPermission('METADATA')) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const featureContentType = Utils.getContentType(
          res.data,
          'model',
          'feature',
        )
        this.setState({ featureContentType: featureContentType })
      })
    }

    this.fetchChangeRequests()
    this.fetchScheduledChangeRequests()

    getGithubIntegration(getStore(), {
      organisation_id: AccountStore.getOrganisation().id,
    }).then((res) => {
      this.setState({
        githubId: res?.data?.results[0]?.id,
        hasIntegrationWithGithub: !!res?.data?.results?.length,
      })
    })
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  setUserOverridesError = () => {
    this.setState({
      userOverrides: [],
      userOverridesError: true,
      userOverridesNoPermission: false,
      userOverridesPaging: { count: 0, currentPage: 1, next: null },
    })
  }

  setUserOverridesNoPermission = () => {
    this.setState({
      userOverrides: [],
      userOverridesError: false,
      userOverridesNoPermission: true,
      userOverridesPaging: { count: 0, currentPage: 1, next: null },
    })
  }

  userOverridesPage = (page, forceRefetch) => {
    if (Utils.getIsEdge()) {
      // Early return if tab should be hidden
      if (Utils.getShouldHideIdentityOverridesTab(ProjectStore.model)) {
        this.setState({
          userOverrides: [],
          userOverridesPaging: {
            count: 0,
            currentPage: 1,
            next: null,
          },
        })
        return
      }

      getPermission(
        getStore(),
        {
          id: this.props.environmentId,
          level: 'environment',
          permissions: 'VIEW_IDENTITIES',
        },
        { forceRefetch },
      )
        .then((permissions) => {
          const hasViewIdentitiesPermission =
            permissions[Utils.getViewIdentitiesPermission()] ||
            permissions.ADMIN
          // Early return if user doesn't have permission
          if (!hasViewIdentitiesPermission) {
            this.setUserOverridesNoPermission()
            return
          }

          data
            .get(
              `${Project.api}environments/${this.props.environmentId}/edge-identity-overrides?feature=${this.props.projectFlag.id}&page=${page}`,
            )
            .then((userOverrides) => {
              this.setState({
                userOverrides: userOverrides.results.map((v) => ({
                  ...v.feature_state,
                  identity: {
                    id: v.identity_uuid,
                    identifier: v.identifier,
                  },
                })),
                userOverridesError: false,
                userOverridesNoPermission: false,
                userOverridesPaging: {
                  count: userOverrides.count,
                  currentPage: page,
                  next: userOverrides.next,
                },
              })
            })
            .catch((response) => {
              if (response?.status === 403) {
                this.setUserOverridesNoPermission()
              } else {
                this.setUserOverridesError()
              }
            })
        })
        .catch(() => {
          this.setUserOverridesError()
        })

      return
    }

    data
      .get(
        `${Project.api}environments/${
          this.props.environmentId
        }/${Utils.getFeatureStatesEndpoint()}/?anyIdentity=1&feature=${
          this.props.projectFlag.id
        }&page=${page}`,
      )
      .then((userOverrides) => {
        this.setState({
          userOverrides: userOverrides.results,
          userOverridesError: false,
          userOverridesNoPermission: false,
          userOverridesPaging: {
            count: userOverrides.count,
            currentPage: page,
            next: userOverrides.next,
          },
        })
      })
      .catch((response) => {
        if (response?.status === 403) {
          this.setUserOverridesNoPermission()
        } else {
          this.setUserOverridesError()
        }
      })
  }

  renderUserOverridesNoResults = () => {
    if (this.state.userOverridesError) {
      return (
        <div className='text-center py-4'>
          Failed to load identity overrides.
        </div>
      )
    }
    if (this.state.userOverridesNoPermission) {
      return (
        <div className='text-center py-4'>
          You do not have permission to view identity overrides.
        </div>
      )
    }
    return (
      <Row className='list-item'>
        <div className='table-column'>
          No identities are overriding this feature.
        </div>
      </Row>
    )
  }

  save = (func, isSaving) => {
    const {
      environmentFlag: propsEnvironmentFlag,
      environmentId,
      identity,
      identityFlag,
      projectFlag: _projectFlag,
      segmentOverrides,
    } = this.props
    const { environmentFlag: stateEnvironmentFlag, projectFlag } = this.state
    const hasMultivariate =
      propsEnvironmentFlag &&
      propsEnvironmentFlag.multivariate_feature_state_values &&
      propsEnvironmentFlag.multivariate_feature_state_values.length
    if (identity) {
      !isSaving &&
        projectFlag.name &&
        func({
          environmentFlag: propsEnvironmentFlag,
          environmentId,
          identity,
          identityFlag: Object.assign({}, identityFlag || {}, {
            enabled: stateEnvironmentFlag.enabled,
            feature_state_value: hasMultivariate
              ? propsEnvironmentFlag.feature_state_value
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

  changeSegment = (items) => {
    const { enabledSegment } = this.state
    items.forEach((item) => {
      item.enabled = enabledSegment
    })
    this.props.updateSegments(items)
    this.setState({ enabledSegment: !enabledSegment })
  }

  changeIdentity = (items) => {
    const { environmentId } = this.props
    const { enabledIndentity } = this.state

    Promise.all(
      items.map(
        (item) =>
          new Promise((resolve) => {
            AppActions.changeUserFlag({
              environmentId,
              identity: item.identity.id,
              identityFlag: item.id,
              onSuccess: resolve,
              payload: {
                enabled: enabledIndentity,
                id: item.identity.id,
                value: item.identity.identifier,
              },
            })
          }),
      ),
    ).then(() => {
      this.userOverridesPage(1)
    })

    this.setState({ enabledIndentity: !enabledIndentity })
  }

  toggleUserFlag = ({ enabled, id, identity }) => {
    const { environmentId } = this.props

    AppActions.changeUserFlag({
      environmentId,
      identity: identity.id,
      identityFlag: id,
      onSuccess: () => {
        this.userOverridesPage(1)
      },
      payload: {
        enabled: !enabled,
        id: identity.id,
        value: identity.identifier,
      },
    })
  }
  parseError = (error) => {
    const { projectFlag } = this.props
    let featureError = error?.message || error?.name?.[0] || error
    let featureWarning = ''
    //Treat multivariate no changes as warnings
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

  addItem = () => {
    const { environmentFlag, environmentId, identity, projectFlag } = this.props
    this.setState({ isLoading: true })
    const selectedIdentity = this.state.selectedIdentity.value
    const identities = identity ? identity.identifier : []

    if (!_.find(identities, (v) => v.identifier === selectedIdentity)) {
      data
        .post(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${selectedIdentity}/${Utils.getFeatureStatesEndpoint()}/`,
          {
            enabled: !environmentFlag.enabled,
            feature: projectFlag.id,
            feature_state_value: environmentFlag.value || null,
          },
        )
        .then(() => {
          this.setState({
            isLoading: false,
            selectedIdentity: null,
          })
          this.userOverridesPage(1)
        })
        .catch((e) => {
          this.setState({ error: e, isLoading: false })
        })
    } else {
      this.setState({
        isLoading: false,
        selectedIdentity: null,
      })
    }
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
    const {
      enabledIndentity,
      enabledSegment,
      environmentFlag,
      featureContentType,
      githubId,
      hasIntegrationWithGithub,
      isEdit,
      projectFlag,
    } = this.state
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
    const isVersionedChangeRequest = existingChangeRequest && isVersioned
    const hideIdentityOverridesTab = Utils.getShouldHideIdentityOverridesTab()
    const noPermissions = this.props.noPermissions
    let regexValid = true

    const isCodeReferencesEnabled = Utils.getFlagsmithHasFeature(
      'git_code_references',
    )

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
              {
                createChangeRequest,
                createFlag,
                editFeatureSegments,
                editFeatureSettings,
                editFeatureValue,
              },
            ) => {
              const saveFeatureValue = saveFeatureWithValidation((schedule) => {
                if ((is4Eyes || schedule) && !identity) {
                  this.setState({ segmentsChanged: false, valueChanged: false })
                  // Until this page and feature-list-store are refactored, this is the best way of parsing feature states
                  const featureStates = (this.props.segmentOverrides || [])
                    .filter((override) => !override.toRemove)
                    .map((override) => {
                      return {
                        enabled: override.enabled,
                        feature: override.feature,
                        feature_segment: {
                          environment: override.environment,
                          id: override.id,
                          is_feature_specific: override.is_feature_specific,
                          priority: override.priority,
                          segment: override.segment,
                          segment_name: override.segment_name,
                          uuid: override.uuid,
                        },
                        feature_state_value: Utils.valueToFeatureState(
                          override.value,
                        ),
                        id: override.id,
                        multivariate_feature_state_values:
                          override.multivariate_options,
                      }
                    })
                    .concat([
                      Object.assign({}, this.props.environmentFlag, {
                        enabled: environmentFlag.enabled,
                        feature_state_value: Utils.valueToFeatureState(
                          environmentFlag.feature_state_value,
                        ),
                        multivariate_feature_state_values:
                          environmentFlag.multivariate_feature_state_values,
                      }),
                    ])

                  const getModalTitle = () => {
                    if (schedule) {
                      return 'New Scheduled Flag Update'
                    }
                    if (this.props.changeRequest) {
                      return 'Update Change Request'
                    }
                    return 'New Change Request'
                  }

                  let modalTitle = 'New Change Request'
                  if (schedule) {
                    modalTitle = 'New Scheduled Flag Update'
                  } else if (this.props.changeRequest) {
                    modalTitle = 'Update Change Request'
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
                                multivariate_options: this.props
                                  .multivariate_options
                                  ? this.props.multivariate_options.map((v) => {
                                      const matching =
                                        projectFlag.multivariate_options.find(
                                          (m) =>
                                            m.id ===
                                            v.multivariate_feature_option,
                                        )
                                      return {
                                        ...v,
                                        percentage_allocation:
                                          matching.default_percentage_allocation,
                                      }
                                    })
                                  : projectFlag.multivariate_options,
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

              const saveSettings = () => {
                this.setState({ settingsChanged: false })
                this.save(editFeatureSettings, isSaving)
              }

              const saveFeatureSegments = saveFeatureWithValidation(
                (schedule) => {
                  this.setState({ segmentsChanged: false })

                  if ((is4Eyes || schedule) && isVersioned && !identity) {
                    return saveFeatureValue()
                  } else {
                    this.save(editFeatureSegments, isSaving)
                  }
                },
              )

              const onCreateFeature = saveFeatureWithValidation(() => {
                this.save(createFlag, isSaving)
              })
              const isLimitReached = false

              const { featureError, featureWarning } = this.parseError(error)

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
                      {({ permission: projectAdmin }) => {
                        this.state.skipSaveProjectFeature = !createFeature
                        const _hasMetadataRequired =
                          this.state.hasMetadataRequired &&
                          !projectFlag.metadata?.length

                        return (
                          <div id='create-feature-modal'>
                            {isEdit && !identity ? (
                              <>
                                <FeaturePipelineStatus
                                  projectId={this.props.projectId}
                                  featureId={projectFlag?.id}
                                />
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
                                  {(!existingChangeRequest ||
                                    isVersionedChangeRequest) && (
                                    <TabItem
                                      data-test='segment_overrides'
                                      tabLabelString='Segment Overrides'
                                      tabLabel={
                                        <Row
                                          className={`justify-content-center ${
                                            this.state.segmentsChanged
                                              ? 'pr-1'
                                              : ''
                                          }`}
                                        >
                                          Segment Overrides{' '}
                                          {this.state.segmentsChanged && (
                                            <div className='unread ml-2 px-2'>
                                              *
                                            </div>
                                          )}
                                        </Row>
                                      }
                                    >
                                      <FormGroup className='mb-4'>
                                        <FeatureInPipelineGuard
                                          projectId={this.props.projectId}
                                          featureId={projectFlag?.id}
                                          renderFallback={(
                                            matchingReleasePipeline,
                                          ) => (
                                            <>
                                              <h5 className='mb-2'>
                                                Segment Overrides{' '}
                                              </h5>
                                              <InfoMessage
                                                title={`Feature in release pipeline`}
                                              >
                                                This feature is in{' '}
                                                <b>
                                                  {
                                                    matchingReleasePipeline?.name
                                                  }
                                                </b>{' '}
                                                release pipeline and no segment
                                                overrides can be created
                                              </InfoMessage>
                                            </>
                                          )}
                                        >
                                          <div>
                                            <Row className='align-items-center mb-2 gap-4 segment-overrides-title'>
                                              <div className='flex-fill'>
                                                <Tooltip
                                                  title={
                                                    <h5 className='mb-0'>
                                                      Segment Overrides{' '}
                                                      <Icon name='info-outlined' />
                                                    </h5>
                                                  }
                                                  place='top'
                                                >
                                                  {
                                                    Constants.strings
                                                      .SEGMENT_OVERRIDES_DESCRIPTION
                                                  }
                                                </Tooltip>
                                              </div>
                                              <Permission
                                                level='environment'
                                                permission={
                                                  'MANAGE_SEGMENT_OVERRIDES'
                                                }
                                                id={this.props.environmentId}
                                              >
                                                {({
                                                  permission:
                                                    manageSegmentOverrides,
                                                }) =>
                                                  !this.state
                                                    .showCreateSegment &&
                                                  !!manageSegmentOverrides &&
                                                  !this.props.disableCreate && (
                                                    <div className='text-right'>
                                                      <Button
                                                        size='small'
                                                        onClick={() => {
                                                          this.setState({
                                                            showCreateSegment: true,
                                                          })
                                                        }}
                                                        theme='outline'
                                                        disabled={
                                                          !!isLimitReached
                                                        }
                                                      >
                                                        Create Feature-Specific
                                                        Segment
                                                      </Button>
                                                    </div>
                                                  )
                                                }
                                              </Permission>
                                              {!this.state.showCreateSegment &&
                                                !noPermissions && (
                                                  <Button
                                                    onClick={() =>
                                                      this.changeSegment(
                                                        this.props
                                                          .segmentOverrides,
                                                      )
                                                    }
                                                    type='button'
                                                    theme='secondary'
                                                    size='small'
                                                  >
                                                    {enabledSegment
                                                      ? 'Enable All'
                                                      : 'Disable All'}
                                                  </Button>
                                                )}
                                            </Row>
                                            {this.props.segmentOverrides ? (
                                              <Permission
                                                level='environment'
                                                permission={
                                                  'MANAGE_SEGMENT_OVERRIDES'
                                                }
                                                id={this.props.environmentId}
                                              >
                                                {({
                                                  permission:
                                                    manageSegmentOverrides,
                                                }) => {
                                                  const isReadOnly =
                                                    !manageSegmentOverrides
                                                  return (
                                                    <>
                                                      <ErrorMessage
                                                        error={featureError}
                                                      />
                                                      <WarningMessage
                                                        warningMessage={
                                                          featureWarning
                                                        }
                                                      />
                                                      <SegmentOverrides
                                                        setShowCreateSegment={(
                                                          showCreateSegment,
                                                        ) =>
                                                          this.setState({
                                                            showCreateSegment,
                                                          })
                                                        }
                                                        readOnly={isReadOnly}
                                                        is4Eyes={is4Eyes}
                                                        showEditSegment
                                                        showCreateSegment={
                                                          this.state
                                                            .showCreateSegment
                                                        }
                                                        feature={projectFlag.id}
                                                        projectId={
                                                          this.props.projectId
                                                        }
                                                        multivariateOptions={
                                                          projectFlag.multivariate_options
                                                        }
                                                        environmentId={
                                                          this.props
                                                            .environmentId
                                                        }
                                                        value={
                                                          this.props
                                                            .segmentOverrides
                                                        }
                                                        controlValue={
                                                          environmentFlag.feature_state_value
                                                        }
                                                        onChange={(v) => {
                                                          this.setState({
                                                            segmentsChanged: true,
                                                          })
                                                          this.props.updateSegments(
                                                            v,
                                                          )
                                                        }}
                                                        highlightSegmentId={
                                                          this.props
                                                            .highlightSegmentId
                                                        }
                                                      />
                                                    </>
                                                  )
                                                }}
                                              </Permission>
                                            ) : (
                                              <div className='text-center'>
                                                <Loader />
                                              </div>
                                            )}
                                            {!this.state.showCreateSegment && (
                                              <ModalHR className='mt-4' />
                                            )}
                                            {!this.state.showCreateSegment && (
                                              <div>
                                                <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                                                  {is4Eyes && isVersioned
                                                    ? 'This will create a change request with any value and segment override changes for the environment'
                                                    : 'This will update the segment overrides for the environment'}{' '}
                                                  <strong>
                                                    {
                                                      _.find(
                                                        project.environments,
                                                        {
                                                          api_key:
                                                            this.props
                                                              .environmentId,
                                                        },
                                                      ).name
                                                    }
                                                  </strong>
                                                </p>
                                                <div className='text-right'>
                                                  <Permission
                                                    level='environment'
                                                    tags={projectFlag.tags}
                                                    permission={Utils.getManageFeaturePermission(
                                                      is4Eyes,
                                                      identity,
                                                    )}
                                                    id={
                                                      this.props.environmentId
                                                    }
                                                  >
                                                    {({
                                                      permission:
                                                        savePermission,
                                                    }) => (
                                                      <Permission
                                                        level='environment'
                                                        permission={
                                                          'MANAGE_SEGMENT_OVERRIDES'
                                                        }
                                                        id={
                                                          this.props
                                                            .environmentId
                                                        }
                                                      >
                                                        {({
                                                          permission:
                                                            manageSegmentsOverrides,
                                                        }) => {
                                                            const getButtonText =
                                                              () => {
                                                                if (isSaving) {
                                                                  return existingChangeRequest
                                                                    ? 'Updating Change Request'
                                                                    : 'Creating Change Request'
                                                                }
                                                                return existingChangeRequest
                                                                  ? 'Update Change Request'
                                                                  : 'Create Change Request'
                                                              }

                                                            const getScheduleButtonText =
                                                              () => {
                                                                if (isSaving) {
                                                                  return existingChangeRequest
                                                                    ? 'Updating Change Request'
                                                                    : 'Scheduling Update'
                                                                }
                                                                return existingChangeRequest
                                                                  ? 'Update Change Request'
                                                                  : 'Schedule Update'
                                                              }

                                                          if (
                                                            isVersioned &&
                                                            is4Eyes
                                                          ) {
                                                            return Utils.renderWithPermission(
                                                              savePermission,
                                                              Utils.getManageFeaturePermissionDescription(
                                                                is4Eyes,
                                                                identity,
                                                              ),
                                                              <Button
                                                                onClick={() =>
                                                                  saveFeatureSegments(
                                                                    false,
                                                                  )
                                                                }
                                                                type='button'
                                                                data-test='update-feature-segments-btn'
                                                                id='update-feature-segments-btn'
                                                                disabled={
                                                                  isSaving ||
                                                                  !projectFlag.name ||
                                                                  invalid ||
                                                                  !savePermission
                                                                }
                                                              >
                                                                  {getButtonText()}
                                                              </Button>,
                                                            )
                                                          }

                                                          return Utils.renderWithPermission(
                                                            manageSegmentsOverrides,
                                                            Constants.environmentPermissions(
                                                              'Manage segment overrides',
                                                            ),
                                                            <>
                                                              {!is4Eyes &&
                                                                isVersioned && (
                                                                  <>
                                                                    <Button
                                                                      feature='SCHEDULE_FLAGS'
                                                                      theme='secondary'
                                                                      onClick={() =>
                                                                        saveFeatureSegments(
                                                                          true,
                                                                        )
                                                                      }
                                                                      className='mr-2'
                                                                      type='button'
                                                                      data-test='create-change-request'
                                                                      id='create-change-request-btn'
                                                                      disabled={
                                                                        isSaving ||
                                                                        !projectFlag.name ||
                                                                        invalid ||
                                                                        !savePermission
                                                                      }
                                                                    >
                                                                        {getScheduleButtonText()}
                                                                    </Button>
                                                                  </>
                                                                )}
                                                              <Button
                                                                onClick={() =>
                                                                  saveFeatureSegments(
                                                                    false,
                                                                  )
                                                                }
                                                                type='button'
                                                                data-test='update-feature-segments-btn'
                                                                id='update-feature-segments-btn'
                                                                disabled={
                                                                  isSaving ||
                                                                  !projectFlag.name ||
                                                                  invalid ||
                                                                  !manageSegmentsOverrides
                                                                }
                                                              >
                                                                {isSaving
                                                                  ? 'Updating'
                                                                  : 'Update Segment Overrides'}
                                                              </Button>
                                                            </>,
                                                          )
                                                        }}
                                                      </Permission>
                                                    )}
                                                  </Permission>
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        </FeatureInPipelineGuard>
                                      </FormGroup>
                                    </TabItem>
                                  )}
                                  <Permission
                                    data-test='identity_overrides'
                                    tabLabel='Identity Overrides'
                                    level='environment'
                                    permission={'VIEW_IDENTITIES'}
                                    id={this.props.environmentId}
                                  >
                                    {({ permission: viewIdentities }) =>
                                      !existingChangeRequest &&
                                      !hideIdentityOverridesTab && (
                                        <TabItem>
                                          {viewIdentities ? (
                                            <>
                                              <FormGroup className='mb-4 mt-2'>
                                                <PanelSearch
                                                  id='users-list'
                                                  className='no-pad identity-overrides-title'
                                                  title={
                                                    <>
                                                      <Tooltip
                                                        title={
                                                          <h5 className='mb-0'>
                                                            Identity Overrides{' '}
                                                            <Icon
                                                              name='info-outlined'
                                                              width={20}
                                                              fill='#9DA4AE'
                                                            />
                                                          </h5>
                                                        }
                                                        place='top'
                                                      >
                                                        {
                                                          Constants.strings
                                                            .IDENTITY_OVERRIDES_DESCRIPTION
                                                        }
                                                      </Tooltip>
                                                      <div className='fw-normal transform-none mt-4'>
                                                        <InfoMessage
                                                          collapseId={
                                                            'identity-overrides'
                                                          }
                                                        >
                                                          Identity overrides
                                                          override feature
                                                          values for individual
                                                          identities. The
                                                          overrides take
                                                          priority over an
                                                          segment overrides and
                                                          environment defaults.
                                                          Identity overrides
                                                          will only apply when
                                                          you identify via the
                                                          SDK.{' '}
                                                          <a
                                                            target='_blank'
                                                            href='https://docs.flagsmith.com/basic-features/managing-identities'
                                                            rel='noreferrer'
                                                          >
                                                            Check the Docs for
                                                            more details
                                                          </a>
                                                          .
                                                        </InfoMessage>
                                                      </div>
                                                    </>
                                                  }
                                                  action={
                                                    !Utils.getIsEdge() && (
                                                      <Button
                                                        onClick={() =>
                                                          this.changeIdentity(
                                                            this.state
                                                              .userOverrides,
                                                          )
                                                        }
                                                        type='button'
                                                        theme='secondary'
                                                        size='small'
                                                      >
                                                        {enabledIndentity
                                                          ? 'Enable All'
                                                          : 'Disable All'}
                                                      </Button>
                                                    )
                                                  }
                                                  items={
                                                    this.state.userOverrides
                                                  }
                                                  paging={
                                                    this.state
                                                      .userOverridesPaging
                                                  }
                                                  renderSearchWithNoResults
                                                  nextPage={() =>
                                                    this.userOverridesPage(
                                                      this.state
                                                        .userOverridesPaging
                                                        .currentPage + 1,
                                                    )
                                                  }
                                                  prevPage={() =>
                                                    this.userOverridesPage(
                                                      this.state
                                                        .userOverridesPaging
                                                        .currentPage - 1,
                                                    )
                                                  }
                                                  goToPage={(page) =>
                                                    this.userOverridesPage(page)
                                                  }
                                                  searchPanel={
                                                    !Utils.getIsEdge() && (
                                                      <div className='text-center mt-2 mb-2'>
                                                        <Flex className='text-left'>
                                                          <IdentitySelect
                                                            isEdge={false}
                                                            ignoreIds={this.state.userOverrides?.map(
                                                              (v) =>
                                                                v.identity?.id,
                                                            )}
                                                            environmentId={
                                                              this.props
                                                                .environmentId
                                                            }
                                                            data-test='select-identity'
                                                            placeholder='Create an Identity Override...'
                                                            value={
                                                              this.state
                                                                .selectedIdentity
                                                            }
                                                            onChange={(
                                                              selectedIdentity,
                                                            ) =>
                                                              this.setState(
                                                                {
                                                                  selectedIdentity,
                                                                },
                                                                this.addItem,
                                                              )
                                                            }
                                                          />
                                                        </Flex>
                                                      </div>
                                                    )
                                                  }
                                                  renderRow={(identityFlag) => {
                                                    const {
                                                      enabled,
                                                      feature_state_value,
                                                      id,
                                                      identity,
                                                    } = identityFlag
                                                    return (
                                                      <Row
                                                        space
                                                        className='list-item cursor-pointer'
                                                        key={id}
                                                      >
                                                        <Row>
                                                          <div
                                                            className='table-column'
                                                            style={{
                                                              width: '65px',
                                                            }}
                                                          >
                                                            <Switch
                                                              checked={enabled}
                                                              onChange={() =>
                                                                this.toggleUserFlag(
                                                                  {
                                                                    enabled,
                                                                    id,
                                                                    identity,
                                                                  },
                                                                )
                                                              }
                                                              disabled={Utils.getIsEdge()}
                                                            />
                                                          </div>
                                                          <div className='font-weight-medium fs-small lh-sm'>
                                                            {
                                                              identity.identifier
                                                            }
                                                          </div>
                                                        </Row>
                                                        <Row>
                                                          <div
                                                            className='table-column'
                                                            style={{
                                                              width: '188px',
                                                            }}
                                                          >
                                                            {feature_state_value !==
                                                              null && (
                                                              <FeatureValue
                                                                value={
                                                                  feature_state_value
                                                                }
                                                              />
                                                            )}
                                                          </div>
                                                          <div className='table-column'>
                                                            <Button
                                                              target='_blank'
                                                              href={`/project/${this.props.projectId}/environment/${this.props.environmentId}/users/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`}
                                                              className='btn btn-link fs-small lh-sm font-weight-medium'
                                                            >
                                                              <Icon
                                                                name='edit'
                                                                width={20}
                                                                fill='#6837FC'
                                                              />{' '}
                                                              Edit
                                                            </Button>
                                                            <Button
                                                              onClick={(e) => {
                                                                e.stopPropagation()
                                                                removeUserOverride(
                                                                  {
                                                                    cb: () =>
                                                                      this.userOverridesPage(
                                                                        1,
                                                                        true,
                                                                      ),
                                                                    environmentId:
                                                                      this.props
                                                                        .environmentId,
                                                                    identifier:
                                                                      identity.identifier,
                                                                    identity:
                                                                      identity.id,
                                                                    identityFlag,
                                                                    projectFlag,
                                                                  },
                                                                )
                                                              }}
                                                              className='btn ml-2 btn-with-icon'
                                                            >
                                                              <Icon
                                                                name='trash-2'
                                                                width={20}
                                                                fill='#656D7B'
                                                              />
                                                            </Button>
                                                          </div>
                                                        </Row>
                                                      </Row>
                                                    )
                                                  }}
                                                  renderNoResults={this.renderUserOverridesNoResults()}
                                                  isLoading={
                                                    !this.state.userOverrides
                                                  }
                                                />
                                              </FormGroup>
                                            </>
                                          ) : (
                                            <InfoMessage>
                                              <div
                                                dangerouslySetInnerHTML={{
                                                  __html:
                                                    Constants.environmentPermissions(
                                                      'View Identities',
                                                    ),
                                                }}
                                              />
                                            </InfoMessage>
                                          )}
                                        </TabItem>
                                      )
                                    }
                                  </Permission>
                                  {!Project.disableAnalytics && (
                                    <TabItem tabLabel={'Analytics'}>
                                      <div className='mb-4'>
                                        <FeatureAnalytics
                                          projectId={`${project.id}`}
                                          featureId={`${projectFlag.id}`}
                                          defaultEnvironmentIds={[
                                            `${environment.id}`,
                                          ]}
                                        />
                                      </div>
                                    </TabItem>
                                  )}
                                  {
                                    <TabItem
                                      data-test='feature_health'
                                      tabLabelString='Feature Health'
                                      tabLabel={
                                        <Row className='d-flex justify-content-center align-items-center pr-1 gap-1'>
                                          <BetaFlag flagName={'feature_health'}>
                                            Feature Health
                                            {this.props.hasUnhealthyEvents && (
                                              <IonIcon
                                                icon={warning}
                                                style={{
                                                  color:
                                                    Constants.featureHealth
                                                      .unhealthyColor,
                                                  marginBottom: -2,
                                                }}
                                              />
                                            )}
                                          </BetaFlag>
                                        </Row>
                                      }
                                    >
                                      <FeatureHealthTabContent
                                        projectId={projectFlag.project}
                                        environmentId={this.props.environmentId}
                                        featureId={projectFlag.id}
                                      />
                                    </TabItem>
                                  }
                                  {isCodeReferencesEnabled && (
                                    <TabItem
                                      tabLabel={
                                        <Row className='justify-content-center'>
                                          Code References
                                        </Row>
                                      }
                                    >
                                      <FeatureCodeReferencesContainer
                                        featureId={projectFlag.id}
                                        projectId={this.props.projectId}
                                      />
                                    </TabItem>
                                  )}
                                  {hasIntegrationWithGithub &&
                                    projectFlag?.id && (
                                      <TabItem
                                        data-test='external-resources-links'
                                        tabLabelString='Links'
                                        tabLabel={
                                          <Row className='justify-content-center'>
                                            Links
                                          </Row>
                                        }
                                      >
                                        <ExternalResourcesLinkTab
                                          githubId={githubId}
                                          organisationId={
                                            AccountStore.getOrganisation().id
                                          }
                                          featureId={projectFlag.id}
                                          projectId={`${this.props.projectId}`}
                                          environmentId={
                                            this.props.environmentId
                                          }
                                        />
                                      </TabItem>
                                    )}
                                  {!existingChangeRequest &&
                                    this.props.flagId &&
                                    isVersioned && (
                                      <TabItem
                                        data-test='change-history'
                                        tabLabel='History'
                                      >
                                        <FeatureHistory
                                          feature={projectFlag.id}
                                          projectId={`${this.props.projectId}`}
                                          environmentId={environment.id}
                                          environmentApiKey={
                                            environment.api_key
                                          }
                                        />
                                      </TabItem>
                                    )}
                                  {!existingChangeRequest && (
                                    <TabItem
                                      data-test='settings'
                                      tabLabelString='Settings'
                                      tabLabel={
                                        <Row className='justify-content-center'>
                                          Settings{' '}
                                          {this.state.settingsChanged && (
                                            <div className='unread ml-2 px-1'>
                                              {'*'}
                                            </div>
                                          )}
                                        </Row>
                                      }
                                    >
                                      <FeatureSettings
                                        projectAdmin={projectAdmin}
                                        createFeature={createFeature}
                                        featureContentType={featureContentType}
                                        identity={identity}
                                        isEdit={isEdit}
                                        projectId={this.props.projectId}
                                        projectFlag={projectFlag}
                                        onChange={(changes) => {
                                          const updates = {}

                                          // Update projectFlag with changes
                                          updates.projectFlag = {
                                            ...this.state.projectFlag,
                                            ...changes,
                                          }

                                          // Set settingsChanged flag unless it's only metadata changing
                                          if (changes.metadata === undefined) {
                                            updates.settingsChanged = true
                                          }

                                          this.setState(updates)
                                        }}
                                        onHasMetadataRequiredChange={(
                                          hasMetadataRequired,
                                        ) =>
                                          this.setState({
                                            hasMetadataRequired,
                                          })
                                        }
                                      />
                                      <JSONReference
                                        className='mb-3'
                                        showNamesButton
                                        title={'Feature'}
                                        json={projectFlag}
                                      />
                                      <ModalHR className='mt-4' />
                                      {isEdit && (
                                        <div className='text-right mt-3'>
                                          {!!createFeature && (
                                            <>
                                              <p className='text-right modal-caption fs-small lh-sm'>
                                                This will save the above
                                                settings{' '}
                                                <strong>
                                                  all environments
                                                </strong>
                                                .
                                              </p>
                                              <Button
                                                onClick={saveSettings}
                                                data-test='update-feature-btn'
                                                id='update-feature-btn'
                                                disabled={
                                                  isSaving ||
                                                  !projectFlag.name ||
                                                  invalid ||
                                                  _hasMetadataRequired
                                                }
                                              >
                                                {isSaving
                                                  ? 'Updating'
                                                  : 'Update Settings'}
                                              </Button>
                                            </>
                                          )}
                                        </div>
                                      )}
                                    </TabItem>
                                  )}
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
                                  featureState={environmentFlag}
                                  projectFlag={projectFlag}
                                  featureContentType={featureContentType}
                                  identity={identity}
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
                                  onHasMetadataRequiredChange={(
                                    hasMetadataRequired,
                                  ) =>
                                    this.setState({
                                      hasMetadataRequired,
                                    })
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
                                  hasMetadataRequired={_hasMetadataRequired}
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
      // toast update feature
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
              segmentsChanged: false,
              settingsChanged: false,
              valueChanged: false,
            })
          } else if (this.props.projectFlag) {
            //update the environmentFlag and projectFlag to the new values
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
              segmentsChanged: false,
              settingsChanged: false,
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

const WrappedCreateFlag = ConfigProvider(withSegmentOverrides(Index))

export default FeatureProvider(WrappedCreateFlag)
