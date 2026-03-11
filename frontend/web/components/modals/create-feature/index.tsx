import React, {
  Component,
  FC,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'
// @ts-ignore untyped module
import _ from 'lodash'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import moment from 'moment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentityProvider from 'common/providers/IdentityProvider'
import FeatureListProvider from 'common/providers/FeatureListProvider'
import AppActions from 'common/dispatcher/app-actions'
import ES6Component from 'common/ES6Component'
import Project from 'common/project'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import classNames from 'classnames'
import JSONReference from 'components/JSONReference'
import { useHasPermission } from 'common/providers/Permission'
import {
  setInterceptClose,
  setModalTitle,
} from 'components/modals/base/ModalDefault'
import ModalHR from 'components/modals/ModalHR'
import { getStore } from 'common/store'
import Button from 'components/base/forms/Button'
import { getGithubIntegration } from 'common/services/useGithubIntegration'
import ExternalResourcesLinkTab from 'components/ExternalResourcesLinkTab'
import { saveFeatureWithValidation } from 'components/saveFeatureWithValidation'
import FeatureHistory from 'components/FeatureHistory'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'
import { getChangeRequests } from 'common/services/useChangeRequest'
import AccountStore from 'common/stores/account-store'
import FeatureHealthTabContent from 'components/feature-health/FeatureHealthTabContent'
import FeaturePipelineStatus from 'components/release-pipelines/FeaturePipelineStatus'
import ProjectProvider from 'common/providers/ProjectProvider'
import CreateFeature from './tabs/CreateFeatureTab'
import FeatureSettings from './tabs/FeatureSettingsTab'
import FeatureValueTab from './tabs/FeatureValueTab'
import IdentityOverridesTab from './tabs/IdentityOverridesTab'
import SegmentOverridesTab from './tabs/SegmentOverridesTab'
import UsageTab from './tabs/UsageTab'
import FeatureLimitAlert from './FeatureLimitAlert'
import FeatureUpdateSummary from './FeatureUpdateSummary'
import FeatureNameInput from './FeatureNameInput'
import {
  EnvironmentPermission,
  ProjectPermission,
} from 'common/types/permissions.types'

type CreateFeatureModalProps = {
  projectFlag?: any
  environmentFlag?: any
  identityFlag?: any
  identity?: string
  identityName?: string
  environmentId: string
  projectId: number
  changeRequest?: any
  flagId?: number
  noPermissions?: boolean
  disableCreate?: boolean
  highlightSegmentId?: number
  defaultExperiment?: boolean
  history?: any
  multivariate_options?: any[]
  segmentOverrides?: any[]
  environmentVariations?: any[]
  updateSegments?: (segments: any[]) => void
  removeMultivariateOption?: (id: number) => void
}

const CreateFeatureModal: FC<CreateFeatureModalProps> = (props) => {
  const {
    changeRequest: existingChangeRequest,
    defaultExperiment,
    disableCreate,
    environmentId,
    environmentVariations,
    flagId,
    highlightSegmentId,
    identity,
    identityName,
    noPermissions,
    projectId,
    removeMultivariateOption,
    segmentOverrides,
    updateSegments,
  } = props

  const [projectFlag, setProjectFlag] = useState<any>(() =>
    props.projectFlag
      ? _.cloneDeep(props.projectFlag)
      : {
          description: undefined,
          is_archived: undefined,
          is_server_key_only: undefined,
          metadata: [],
          multivariate_options: [],
          name: undefined,
          tags: [],
        },
  )

  const [environmentFlag, setEnvironmentFlag] = useState<any>(() => {
    const sourceFlag = props.identityFlag || props.environmentFlag
    return sourceFlag ? _.cloneDeep(sourceFlag) : {}
  })

  const [_changeRequests, setChangeRequests] = useState<any[]>([])
  const [_scheduledChangeRequests, setScheduledChangeRequests] = useState<
    any[]
  >([])
  const [valueChanged, setValueChanged] = useState(false)
  const [settingsChanged, setSettingsChanged] = useState(false)
  const [segmentsChanged, setSegmentsChanged] = useState(false)
  const [hasMetadataRequired, setHasMetadataRequired] = useState(false)
  const [featureLimitAlert, setFeatureLimitAlert] = useState({
    percentage: 0,
  })
  const [hasIntegrationWithGithub, setHasIntegrationWithGithub] =
    useState(false)
  const [githubId, setGithubId] = useState('')
  const [skipSaveProjectFeature, setSkipSaveProjectFeature] = useState(false)
  const [, setTabKey] = useState(0)

  const isEdit = !!props.projectFlag
  const focusTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const close = useCallback(() => {
    closeModal()
  }, [])

  const onClosing = useCallback(() => {
    if (isEdit) {
      return new Promise<boolean>((resolve) => {
        if (settingsChanged || valueChanged || segmentsChanged) {
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
  }, [isEdit, settingsChanged, valueChanged, segmentsChanged])

  const fetchChangeRequests = useCallback(
    (forceRefetch?: boolean) => {
      if (!props.projectFlag?.id) return

      getChangeRequests(
        getStore(),
        {
          committed: false,
          environmentId,
          feature_id: props.projectFlag?.id,
        },
        { forceRefetch },
      ).then((res: any) => {
        setChangeRequests(res.data?.results)
      })
    },
    [environmentId, props.projectFlag?.id],
  )

  const fetchScheduledChangeRequests = useCallback(
    (forceRefetch?: boolean) => {
      if (!props.projectFlag?.id) return

      const date = moment().toISOString()

      getChangeRequests(
        getStore(),
        {
          environmentId,
          feature_id: props.projectFlag.id,
          live_from_after: date,
        },
        { forceRefetch },
      ).then((res: any) => {
        setScheduledChangeRequests(res.data?.results)
      })
    },
    [environmentId, props.projectFlag?.id],
  )

  // Mount effects
  useEffect(() => {
    setInterceptClose(onClosing)
  }, [onClosing])

  useEffect(() => {
    fetchChangeRequests()
    fetchScheduledChangeRequests()

    getGithubIntegration(getStore(), {
      organisation_id: AccountStore.getOrganisation().id,
    }).then((res: any) => {
      setGithubId(res?.data?.results[0]?.id)
      setHasIntegrationWithGithub(!!res?.data?.results?.length)
    })

    const timeout = focusTimeoutRef.current
    return () => {
      if (timeout) {
        clearTimeout(timeout)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Sync environmentFlag from props when updated_at changes
  useEffect(() => {
    const source = props.identityFlag || props.environmentFlag
    if (source?.updated_at) {
      setEnvironmentFlag(_.cloneDeep(source))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [(props.identityFlag || props.environmentFlag)?.updated_at])

  // Sync projectFlag from props when updated_at changes
  useEffect(() => {
    if (props.projectFlag?.updated_at) {
      setProjectFlag(_.cloneDeep(props.projectFlag))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.projectFlag?.updated_at])

  // Sync multivariate options from environment variations
  useEffect(() => {
    if (!identity && environmentVariations?.length) {
      setProjectFlag((prev: any) => ({
        ...prev,
        multivariate_options: prev.multivariate_options?.map((v: any) => {
          const matchingVariation = (
            props.multivariate_options || environmentVariations
          ).find((e: any) => e.multivariate_feature_option === v.id)
          return {
            ...v,
            default_percentage_allocation:
              (matchingVariation && matchingVariation.percentage_allocation) ||
              v.default_percentage_allocation ||
              0,
          }
        }),
      }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environmentVariations])

  const cleanInputValue = (value: any) => {
    if (value && typeof value === 'string') {
      return value.trim()
    }
    return value
  }

  const parseError = (error: any) => {
    let featureError =
      error?.metadata
        ?.flatMap((m: any) => m.non_field_errors ?? [])
        .join('\n') ||
      error?.message ||
      error?.name?.[0] ||
      error
    let featureWarning = ''
    if (
      featureError?.includes?.('no changes') &&
      props.projectFlag?.multivariate_options?.length
    ) {
      featureWarning =
        'Your feature contains no changes to its value, enabled state or environment weights. If you have adjusted any variation values this will have been saved for all environments.'
      featureError = ''
    }
    return { featureError, featureWarning }
  }

  const save = (func: (...args: any[]) => void, isSaving: boolean) => {
    const hasMultivariate =
      props.environmentFlag?.multivariate_feature_state_values?.length

    if (identity) {
      !isSaving &&
        projectFlag.name &&
        func({
          environmentFlag: props.environmentFlag,
          environmentId,
          identity,
          identityFlag: Object.assign({}, props.identityFlag || {}, {
            enabled: environmentFlag.enabled,
            feature_state_value: hasMultivariate
              ? props.environmentFlag.feature_state_value
              : cleanInputValue(environmentFlag.feature_state_value),
            multivariate_options:
              environmentFlag.multivariate_feature_state_values,
          }),
          projectFlag,
        })
    } else {
      FeatureListStore.isSaving = true
      FeatureListStore.trigger('change')
      !isSaving &&
        projectFlag.name &&
        func(
          projectId,
          environmentId,
          {
            default_enabled: environmentFlag.enabled,
            description: projectFlag.description,
            initial_value: cleanInputValue(environmentFlag.feature_state_value),
            is_archived: projectFlag.is_archived,
            is_server_key_only: projectFlag.is_server_key_only,
            metadata:
              !props.projectFlag?.metadata ||
              (props.projectFlag.metadata !== projectFlag.metadata &&
                projectFlag.metadata.length)
                ? projectFlag.metadata
                : props.projectFlag.metadata,
            multivariate_options: projectFlag.multivariate_options,
            name: projectFlag.name,
            tags: projectFlag.tags,
          },
          {
            skipSaveProjectFeature,
            ...props.projectFlag,
          },
          {
            ...props.environmentFlag,
            multivariate_feature_state_values:
              environmentVariations ||
              props.environmentFlag?.multivariate_feature_state_values,
          },
          segmentOverrides,
        )
    }
  }

  const environment = ProjectStore.getEnvironment(environmentId) as any
  const isVersioned = !!environment?.use_v2_feature_versioning
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)

  const { permission: createFeaturePermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.CREATE_FEATURE,
  })

  const { permission: savePermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getManageFeaturePermission(is4Eyes, identity),
    tags: projectFlag.tags,
  })

  useEffect(() => {
    setSkipSaveProjectFeature(!createFeaturePermission)
  }, [createFeaturePermission])
  const project = ProjectStore.model as any
  const caseSensitive = project?.only_allow_lower_case_feature_names
  const regex = project?.feature_name_regex
  const controlValue = Utils.calculateControl(projectFlag.multivariate_options)
  const invalid =
    !!projectFlag.multivariate_options &&
    projectFlag.multivariate_options.length &&
    controlValue < 0
  const isVersionedChangeRequest = existingChangeRequest && isVersioned
  const hideIdentityOverridesTab = Utils.getShouldHideIdentityOverridesTab()
  const hasCodeReferences = projectFlag?.code_references_counts?.length > 0

  let regexValid = true
  try {
    if (!isEdit && projectFlag.name && regex) {
      regexValid = !!projectFlag.name.match(new RegExp(regex))
    }
  } catch (e) {
    regexValid = false
  }

  return (
    <ProjectProvider id={projectId}>
      {({ project }: any) => {
        const Provider = identity ? IdentityProvider : FeatureListProvider
        return (
          <Provider
            onSave={() => {
              if (identity) {
                close()
              }
              AppActions.refreshFeatures(projectId, environmentId)

              if (is4Eyes && !identity) {
                fetchChangeRequests(true)
                fetchScheduledChangeRequests(true)
              }

              if (existingChangeRequest) {
                close()
              }
            }}
          >
            {(
              { error, isSaving }: any,
              {
                createChangeRequest,
                createFlag,
                editFeatureSegments,
                editFeatureSettings,
                editFeatureValue,
              }: any,
            ) => {
              const saveFeatureValue = saveFeatureWithValidation(
                (schedule?: boolean) => {
                  if ((is4Eyes || schedule) && !identity) {
                    setSegmentsChanged(false)
                    setValueChanged(false)
                    const featureStates = (segmentOverrides || [])
                      .filter((override: any) => !override.toRemove)
                      .map((override: any) => ({
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
                      }))
                      .concat([
                        Object.assign({}, props.environmentFlag, {
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
                      if (existingChangeRequest) {
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
                        changeRequest={existingChangeRequest}
                        projectId={projectId}
                        environmentId={ProjectStore.getEnvironmentIdFromKey(
                          environmentId,
                        )}
                        featureId={projectFlag.id}
                        featureStates={featureStates as any}
                        onSave={({
                          approvals,
                          description,
                          ignore_conflicts,
                          live_from,
                          title,
                        }: any) => {
                          closeModal2()
                          save(
                            (
                              _projectId: any,
                              _environmentId: any,
                              flag: any,
                              _projectFlag: any,
                              _environmentFlag: any,
                              _segmentOverrides: any,
                            ) => {
                              createChangeRequest(
                                _projectId,
                                _environmentId,
                                flag,
                                _projectFlag,
                                _environmentFlag,
                                _segmentOverrides,
                                {
                                  approvals,
                                  description,
                                  featureStateId:
                                    existingChangeRequest?.feature_states?.[0]
                                      ?.id,
                                  id: existingChangeRequest?.id,
                                  ignore_conflicts,
                                  live_from,
                                  multivariate_options:
                                    flag.multivariate_options,
                                  title,
                                },
                                !is4Eyes,
                              )
                            },
                            isSaving,
                          )
                        }}
                      />,
                    )
                  } else {
                    setValueChanged(false)
                    save(editFeatureValue, isSaving)
                  }
                },
              )

              const saveSettings = () => {
                setSettingsChanged(false)
                save(editFeatureSettings, isSaving)
              }

              const saveFeatureSegments = saveFeatureWithValidation(
                (schedule?: boolean) => {
                  setSegmentsChanged(false)

                  if ((is4Eyes || schedule) && isVersioned && !identity) {
                    return saveFeatureValue(false)
                  } else {
                    save(editFeatureSegments, isSaving)
                  }
                },
              )

              const onCreateFeature = saveFeatureWithValidation(() => {
                save(createFlag, isSaving)
              })

              const { featureError, featureWarning } = parseError(error)

              return (
                <div id='create-feature-modal'>
                  {isEdit && !identity ? (
                    <>
                      <FeaturePipelineStatus
                        projectId={`${projectId}`}
                        featureId={projectFlag?.id}
                      />
                      <Tabs
                        urlParam='tab'
                        history={props.history}
                        onChange={() => setTabKey((k) => k + 1)}
                        overflowX
                      >
                        <TabItem
                          data-test='value'
                          tabLabelString='Value'
                          tabLabel={
                            <Row className='justify-content-center'>
                              Value{' '}
                              {valueChanged && (
                                <div className='unread ml-2 px-1'>{'*'}</div>
                              )}
                            </Row>
                          }
                        >
                          <FeatureValueTab
                            error={error}
                            projectId={projectId}
                            noPermissions={!!noPermissions}
                            featureState={environmentFlag}
                            projectFlag={projectFlag}
                            onEnvironmentFlagChange={(changes: any) => {
                              setEnvironmentFlag((prev: any) => ({
                                ...prev,
                                ...changes,
                              }))
                              setValueChanged(true)
                            }}
                            onProjectFlagChange={(changes: any) => {
                              setProjectFlag((prev: any) => ({
                                ...prev,
                                ...changes,
                              }))
                            }}
                            onRemoveMultivariateOption={
                              removeMultivariateOption
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
                            json={props.environmentFlag}
                          />
                          <FlagValueFooter
                            is4Eyes={is4Eyes}
                            isVersioned={isVersioned}
                            projectId={projectId}
                            projectFlag={projectFlag}
                            environmentId={environmentId}
                            environmentName={
                              _.find(project.environments, {
                                api_key: environmentId,
                              })?.name || ''
                            }
                            isSaving={isSaving}
                            featureName={projectFlag.name}
                            isInvalid={invalid}
                            existingChangeRequest={existingChangeRequest}
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
                                  segmentsChanged ? 'pr-1' : ''
                                }`}
                              >
                                Segment Overrides{' '}
                                {segmentsChanged && (
                                  <div className='unread ml-2 px-2'>*</div>
                                )}
                              </Row>
                            }
                          >
                            <SegmentOverridesTab
                              projectId={projectId}
                              environmentId={environmentId}
                              projectFlag={projectFlag}
                              segmentOverrides={segmentOverrides}
                              updateSegments={updateSegments!}
                              controlValue={environmentFlag.feature_state_value}
                              onSegmentsChange={() => setSegmentsChanged(true)}
                              saveFeatureSegments={saveFeatureSegments}
                              isSaving={isSaving}
                              invalid={invalid}
                              featureError={featureError}
                              featureWarning={featureWarning}
                              existingChangeRequest={existingChangeRequest}
                              noPermissions={!!noPermissions}
                              disableCreate={disableCreate}
                              highlightSegmentId={highlightSegmentId}
                            />
                          </TabItem>
                        )}
                        {!existingChangeRequest &&
                          !hideIdentityOverridesTab && (
                            <TabItem
                              data-test='identity_overrides'
                              tabLabel='Identity Overrides'
                            >
                              <IdentityOverridesTab
                                environmentId={environmentId}
                                projectId={projectId}
                                projectFlag={projectFlag}
                                environmentFlag={props.environmentFlag}
                              />
                            </TabItem>
                          )}
                        {(!Project.disableAnalytics || hasCodeReferences) && (
                          <TabItem
                            tabLabelString='Usage'
                            tabLabel={
                              <Row className='justify-content-center'>
                                Usage
                              </Row>
                            }
                          >
                            <UsageTab
                              projectId={project.id}
                              featureId={projectFlag.id}
                              environmentId={environment.id}
                              hasCodeReferences={hasCodeReferences}
                            />
                          </TabItem>
                        )}
                        {
                          <TabItem
                            data-test='feature_health'
                            tabLabelString='Health'
                            tabLabel={'Health'}
                          >
                            <FeatureHealthTabContent
                              projectId={projectFlag.project}
                              environmentId={ProjectStore.getEnvironmentIdFromKey(
                                environmentId,
                              )}
                              featureId={projectFlag.id}
                            />
                          </TabItem>
                        }
                        {hasIntegrationWithGithub && projectFlag?.id && (
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
                              organisationId={AccountStore.getOrganisation().id}
                              featureId={projectFlag.id}
                              projectId={projectId}
                              environmentId={ProjectStore.getEnvironmentIdFromKey(
                                environmentId,
                              )}
                            />
                          </TabItem>
                        )}
                        {!existingChangeRequest && flagId && isVersioned && (
                          <TabItem
                            data-test='change-history'
                            tabLabel='History'
                          >
                            <FeatureHistory
                              feature={projectFlag.id}
                              projectId={`${projectId}`}
                              environmentId={environment.id}
                              environmentApiKey={environment.api_key}
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
                                {settingsChanged && (
                                  <div className='unread ml-2 px-1'>{'*'}</div>
                                )}
                              </Row>
                            }
                          >
                            <FeatureSettings
                              identity={identity}
                              projectId={projectId}
                              projectFlag={projectFlag}
                              onChange={(changes: any) => {
                                setProjectFlag((prev: any) => ({
                                  ...prev,
                                  ...changes,
                                }))
                                if (changes.metadata === undefined) {
                                  setSettingsChanged(true)
                                }
                              }}
                              onHasMetadataRequiredChange={
                                setHasMetadataRequired
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
                                {!!createFeaturePermission && (
                                  <>
                                    <p className='text-right modal-caption fs-small lh-sm'>
                                      This will save the above settings{' '}
                                      <strong>all environments</strong>.
                                    </p>
                                    <Button
                                      onClick={saveSettings}
                                      data-test='update-feature-btn'
                                      id='update-feature-btn'
                                      disabled={
                                        isSaving ||
                                        !projectFlag.name ||
                                        invalid ||
                                        hasMetadataRequired
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
                        projectId={projectId}
                        onChange={setFeatureLimitAlert}
                      />
                      <div className={identity ? 'px-3' : ''}>
                        <FeatureNameInput
                          value={projectFlag.name}
                          onChange={(name: string) =>
                            setProjectFlag((prev: any) => ({
                              ...prev,
                              name,
                            }))
                          }
                          caseSensitive={caseSensitive}
                          regex={regex}
                          regexValid={regexValid}
                          autoFocus
                        />
                      </div>
                      <CreateFeature
                        projectId={projectId}
                        error={error}
                        featureState={props.environmentFlag || environmentFlag}
                        projectFlag={projectFlag}
                        identity={identity}
                        defaultExperiment={defaultExperiment}
                        overrideFeatureState={
                          props.identityFlag ? environmentFlag : null
                        }
                        onEnvironmentFlagChange={(changes: any) => {
                          setEnvironmentFlag((prev: any) => ({
                            ...prev,
                            ...changes,
                          }))
                          setValueChanged(true)
                        }}
                        onProjectFlagChange={(changes: any) => {
                          setProjectFlag((prev: any) => ({
                            ...prev,
                            ...changes,
                          }))
                        }}
                        onRemoveMultivariateOption={removeMultivariateOption}
                        onHasMetadataRequiredChange={setHasMetadataRequired}
                        featureError={parseError(error).featureError}
                        featureWarning={parseError(error).featureWarning}
                      />
                      <FeatureUpdateSummary
                        identity={identity}
                        onCreateFeature={onCreateFeature}
                        isSaving={isSaving}
                        name={projectFlag.name}
                        invalid={invalid}
                        regexValid={regexValid}
                        featureLimitPercentage={featureLimitAlert.percentage}
                        hasMetadataRequired={hasMetadataRequired}
                      />
                    </div>
                  )}
                  {identity && (
                    <div className='pr-3'>
                      {identity ? (
                        <div className='mb-3 mt-4'>
                          <p className='text-left ml-3 modal-caption fs-small lh-small'>
                            This will update the feature value for the user{' '}
                            <strong>{identityName}</strong> in
                            <strong>
                              {' '}
                              {
                                _.find(project.environments, {
                                  api_key: environmentId,
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
                        {identity &&
                          Utils.renderWithPermission(
                            savePermission,
                            EnvironmentPermission.UPDATE_FEATURE_STATE,
                            <div>
                              <Button
                                onClick={() => saveFeatureValue()}
                                data-test='update-feature-btn'
                                id='update-feature-btn'
                                disabled={
                                  !savePermission ||
                                  isSaving ||
                                  !projectFlag.name ||
                                  invalid
                                }
                              >
                                {isSaving ? 'Updating' : 'Update Feature'}
                              </Button>
                            </div>,
                          )}
                      </div>
                    </div>
                  )}
                </div>
              )
            }}
          </Provider>
        )
      }}
    </ProjectProvider>
  )
}

CreateFeatureModal.displayName = 'create-feature'

// This component remounts the modal when a feature is created
class FeatureProvider extends Component<any, any> {
  constructor(props: any) {
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
      }: any = {}) => {
        if (error?.data?.metadata) {
          error.data.metadata?.forEach((m: any) => {
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
            (flag: any) => flag.name === createdFlag,
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
          const newEnvironmentFlag = envFlags?.[this.props.projectFlag.id] || {}
          const newProjectFlag = FeatureListStore.getProjectFlags()?.find?.(
            (flag: any) => flag.id === this.props.projectFlag.id,
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

  listenTo: any

  render() {
    return (
      <WrappedCreateFlag
        key={this.state.projectFlag?.id || 'new'}
        {...this.state}
      />
    )
  }
}

const WrappedCreateFlag = ConfigProvider(
  withSegmentOverrides(CreateFeatureModal),
)

export default FeatureProvider
