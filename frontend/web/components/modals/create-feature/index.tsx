import React, { FC, useCallback, useEffect, useRef, useState } from 'react'
import cloneDeep from 'lodash/cloneDeep'
import moment from 'moment'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { useHasGithubIntegration } from 'common/hooks/useHasGithubIntegration'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentityProvider from 'common/providers/IdentityProvider'
import FeatureListProvider from 'common/providers/FeatureListProvider'
import AppActions from 'common/dispatcher/app-actions'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import classNames from 'classnames'
import { useHasPermission } from 'common/providers/Permission'
import { setInterceptClose } from 'components/modals/base/ModalDefault'
import { getStore } from 'common/store'
import ExternalResourcesLinkTab from 'components/ExternalResourcesLinkTab'
import { saveFeatureWithValidation } from 'components/saveFeatureWithValidation'
import FeatureHistory from 'components/FeatureHistory'
import { getChangeRequests } from 'common/services/useChangeRequest'
import FeatureHealthTabContent from 'components/feature-health/FeatureHealthTabContent'
import FeaturePipelineStatus from 'components/release-pipelines/FeaturePipelineStatus'
import { History } from 'history'
import CreateFeature from './tabs/CreateFeatureTab'
import FeatureSettings from './tabs/FeatureSettingsTab'
import FeatureValueTab from './tabs/FeatureValueTab'
import IdentityOverridesTab from './tabs/IdentityOverridesTab'
import SegmentOverridesTab, {
  SegmentOverrideValue,
} from './tabs/SegmentOverridesTab'
import UsageTab from './tabs/UsageTab'
import FeatureLimitAlert from './components/FeatureLimitAlert'
import FeatureUpdateSummary from './components/FeatureUpdateSummary'
import FeatureNameInput from './components/FeatureNameInput'
import IdentitySaveFooter from './components/IdentitySaveFooter'
import { ProjectPermission } from 'common/types/permissions.types'
import type {
  ChangeRequest,
  FeatureState,
  MultivariateFeatureStateValue,
  ProjectFlag,
} from 'common/types/responses'

type CreateFeatureModalProps = {
  projectFlag?: ProjectFlag
  environmentFlag?: FeatureState
  identityFlag?: FeatureState
  identity?: string
  identityName?: string
  environmentId: string
  projectId: number
  changeRequest?: ChangeRequest
  noPermissions?: boolean
  disableCreate?: boolean
  highlightSegmentId?: number
  defaultExperiment?: boolean
  history?: History
  multivariate_options?: MultivariateFeatureStateValue[]
} & Partial<InjectedSegmentOverrideProps>

type InjectedSegmentOverrideProps = {
  segmentOverrides: SegmentOverrideValue[]
  environmentVariations: MultivariateFeatureStateValue[]
  updateSegments: (segments: SegmentOverrideValue[]) => void
  removeMultivariateOption: (id: number) => void
}

const CreateFeatureModal: FC<CreateFeatureModalProps> = (props) => {
  const {
    changeRequest: existingChangeRequest,
    defaultExperiment,
    disableCreate,
    environmentId,
    environmentVariations,
    highlightSegmentId,
    identity,
    identityName,
    noPermissions,
    projectId,
    removeMultivariateOption,
    segmentOverrides,
    updateSegments,
  } = props
  const flagId = props.environmentFlag?.id

  const [projectFlag, setProjectFlag] = useState<any>(() =>
    props.projectFlag
      ? cloneDeep(props.projectFlag)
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
    return sourceFlag ? cloneDeep(sourceFlag) : {}
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
  const [skipSaveProjectFeature, setSkipSaveProjectFeature] = useState(false)
  const [ownerIds, setOwnerIds] = useState<number[]>([])
  const [groupOwnerIds, setGroupOwnerIds] = useState<number[]>([])
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
      setEnvironmentFlag(cloneDeep(source))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [(props.identityFlag || props.environmentFlag)?.updated_at])

  // Sync projectFlag from props only when the flag ID changes (e.g. navigating
  // to a different feature). We intentionally avoid syncing on every reference
  // change, as the parent Provider re-creates the object on saves, which would
  // overwrite the user's unsaved edits to settings/tags/description.
  useEffect(() => {
    if (props.projectFlag) {
      setProjectFlag(cloneDeep(props.projectFlag))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.projectFlag?.id])

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
              ? props.environmentFlag?.feature_state_value
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
            ...(ownerIds.length ? { owners: ownerIds } : {}),
            ...(groupOwnerIds.length ? { group_owners: groupOwnerIds } : {}),
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

  const { getEnvironment, project } = useProjectEnvironments(projectId)
  const environment = getEnvironment(environmentId)

  const isVersioned = !!environment?.use_v2_feature_versioning
  const is4Eyes = Utils.changeRequestsEnabled(
    environment?.minimum_change_request_approvals,
  )

  const {
    githubId,
    hasIntegration: hasIntegrationWithGithub,
    organisationId,
  } = useHasGithubIntegration()

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

  if (!environment || !project) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const caseSensitive = !!project.only_allow_lower_case_feature_names
  const regex = project.feature_name_regex ?? undefined
  const controlValue = Utils.calculateControl(projectFlag.multivariate_options)
  const invalid =
    !!projectFlag.multivariate_options &&
    projectFlag.multivariate_options.length &&
    controlValue < 0
  const isVersionedChangeRequest = existingChangeRequest && isVersioned
  const hideIdentityOverridesTab = Utils.getShouldHideIdentityOverridesTab()

  let regexValid = true
  try {
    if (!isEdit && projectFlag.name && regex) {
      regexValid = !!projectFlag.name.match(new RegExp(regex))
    }
  } catch (e) {
    regexValid = false
  }

  const Provider = identity ? IdentityProvider : FeatureListProvider
  const environmentName = environment.name

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
        { error, isSaving }: { error: any; isSaving: boolean },
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
              const segmentFeatureStates = (segmentOverrides || [])
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
              const featureStates = [
                ...segmentFeatureStates,
                {
                  ...props.environmentFlag,
                  enabled: environmentFlag.enabled,
                  feature_state_value: Utils.valueToFeatureState(
                    environmentFlag.feature_state_value,
                  ),
                  multivariate_feature_state_values:
                    environmentFlag.multivariate_feature_state_values,
                },
              ]

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
                  environmentId={environment.id}
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
                              existingChangeRequest?.feature_states?.[0]?.id,
                            id: existingChangeRequest?.id,
                            ignore_conflicts,
                            live_from,
                            multivariate_options: flag.multivariate_options,
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
              return saveFeatureValue(schedule)
            } else {
              save(editFeatureSegments, isSaving)
            }
          },
        )

        const onCreateFeature = saveFeatureWithValidation(() => {
          save(createFlag, isSaving)
        })

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
                      environmentFlag={props.environmentFlag}
                      environmentId={environmentId}
                      environmentName={environmentName}
                      is4Eyes={is4Eyes}
                      isVersioned={isVersioned}
                      isSaving={isSaving}
                      existingChangeRequest={!!existingChangeRequest}
                      onSaveFeatureValue={saveFeatureValue}
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
                    />
                  </TabItem>
                  {(!existingChangeRequest || isVersionedChangeRequest) &&
                    updateSegments && (
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
                          updateSegments={updateSegments}
                          controlValue={environmentFlag.feature_state_value}
                          onSegmentsChange={() => setSegmentsChanged(true)}
                          saveFeatureSegments={saveFeatureSegments}
                          isSaving={isSaving}
                          invalid={invalid}
                          error={error}
                          existingChangeRequest={existingChangeRequest}
                          noPermissions={!!noPermissions}
                          disableCreate={disableCreate}
                          highlightSegmentId={highlightSegmentId}
                        />
                      </TabItem>
                    )}
                  {!existingChangeRequest && !hideIdentityOverridesTab && (
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
                  <TabItem
                    tabLabelString='Usage'
                    tabLabel={
                      <Row className='justify-content-center'>Usage</Row>
                    }
                  >
                    <UsageTab
                      projectId={projectId}
                      featureId={projectFlag.id}
                      environmentId={environment.id}
                    />
                  </TabItem>
                  {
                    <TabItem
                      data-test='feature_health'
                      tabLabelString='Health'
                      tabLabel={'Health'}
                    >
                      <FeatureHealthTabContent
                        projectId={projectFlag.project}
                        environmentId={environment.id}
                        featureId={projectFlag.id}
                      />
                    </TabItem>
                  }
                  {hasIntegrationWithGithub && projectFlag?.id && (
                    <TabItem
                      data-test='external-resources-links'
                      tabLabelString='Links'
                      tabLabel={
                        <Row className='justify-content-center'>Links</Row>
                      }
                    >
                      <ExternalResourcesLinkTab
                        githubId={githubId}
                        organisationId={organisationId}
                        featureId={projectFlag.id}
                        projectId={projectId}
                        environmentId={`${environment.id}`}
                      />
                    </TabItem>
                  )}
                  {!existingChangeRequest && flagId && isVersioned && (
                    <TabItem data-test='change-history' tabLabel='History'>
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
                        isSaving={isSaving}
                        invalid={invalid}
                        hasMetadataRequired={hasMetadataRequired}
                        onChange={(changes: any) => {
                          setProjectFlag((prev: any) => ({
                            ...prev,
                            ...changes,
                          }))
                          if (changes.metadata === undefined) {
                            setSettingsChanged(true)
                          }
                        }}
                        onHasMetadataRequiredChange={setHasMetadataRequired}
                        onSaveSettings={saveSettings}
                      />
                    </TabItem>
                  )}
                </Tabs>
              </>
            ) : (
              <div
                className={classNames(!isEdit ? 'create-feature-tab px-3' : '')}
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
                  ownerIds={ownerIds}
                  groupOwnerIds={groupOwnerIds}
                  onOwnerIdsChange={setOwnerIds}
                  onGroupOwnerIdsChange={setGroupOwnerIds}
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
                  projectId={projectId}
                  identity={identity}
                  onCreateFeature={onCreateFeature}
                  isSaving={isSaving}
                  name={projectFlag.name}
                  invalid={invalid}
                  regexValid={regexValid}
                  featureLimitPercentage={featureLimitAlert.percentage}
                  hasMetadataRequired={hasMetadataRequired}
                  ownerIds={ownerIds}
                  groupOwnerIds={groupOwnerIds}
                />
              </div>
            )}
            {identity && (
              <IdentitySaveFooter
                identityName={identityName}
                environmentName={environmentName}
                savePermission={savePermission}
                isSaving={isSaving}
                projectFlagName={projectFlag.name}
                invalid={invalid}
                onSave={() => saveFeatureValue()}
              />
            )}
          </div>
        )
      }}
    </Provider>
  )
}

import ConfigProvider from 'common/providers/ConfigProvider'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import withFeatureProvider from './hoc/FeatureProvider'

export default withFeatureProvider(
  ConfigProvider(withSegmentOverrides(CreateFeatureModal)),
)
