import React, { FC, useCallback, useEffect, useRef, useState } from 'react'
import { useHistory } from 'react-router-dom'
import moment from 'moment'
import Constants from 'common/constants'
import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import FeatureListStore from 'common/stores/feature-list-store'
import FeatureListProvider from 'common/providers/FeatureListProvider'
import IdentityProvider from 'common/providers/IdentityProvider'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import SegmentOverrides from 'components/SegmentOverrides'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import ErrorMessage from 'components/ErrorMessage'
import { useHasPermission } from 'common/providers/Permission'
import IdentitySelect from 'components/IdentitySelect'
import { setInterceptClose } from 'components/modals/base/ModalDefault'
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
import FeatureSettings from './tabs/FeatureSettings'
import FeatureValueTab from './tabs/FeatureValue'
import CreateFeatureView from './CreateFeatureView'
import Project from 'common/project'
import {
  ChangeRequest,
  ChangeRequestSummary,
  FeatureState,
  FlagsmithValue,
  Project as ProjectType,
  ProjectFlag,
} from 'common/types/responses'

type CreateFeatureModalProps = {
  projectId: number
  environmentId: string
  flagId?: number
  projectFlag?: ProjectFlag
  environmentFlag?: FeatureState
  identityFlag?: FeatureState
  identity?: string
  identityName?: string
  changeRequest?: ChangeRequest
  highlightSegmentId?: number
  disableCreate?: boolean
  noPermissions?: boolean
  hasUnhealthyEvents?: boolean
  // HOC-injected props (from withSegmentOverrides, ConfigProvider)
  segmentOverrides?: FeatureState[]
  updateSegments: (segmentOverrides: FeatureState[]) => void
  removeMultivariateOption: (id: number) => void
  environmentVariations?: any[]
}

type UserOverrideType = FeatureState & {
  identity: { id: string; identifier: string }
}

type SelectedIdentity = { value: string; label?: string }

const CreateFeatureModal: FC<CreateFeatureModalProps> = (props) => {
  const {
    changeRequest: existingChangeRequest,
    disableCreate,
    environmentFlag: propsEnvironmentFlag,
    environmentId,
    environmentVariations,
    flagId,
    hasUnhealthyEvents,
    highlightSegmentId,
    identity,
    identityFlag,
    identityName,
    noPermissions,
    projectFlag: propsProjectFlag,
    projectId,
    removeMultivariateOption,
    segmentOverrides,
    updateSegments,
  } = props

  const history = useHistory()
  const isEdit = !!propsProjectFlag

  // Initialize state
  const [_changeRequests, setChangeRequests] = useState<ChangeRequestSummary[]>(
    [],
  )
  const [enabledIndentity, setEnabledIndentity] = useState(false)
  const [enabledSegment, setEnabledSegment] = useState(false)
  const [environmentFlag, setEnvironmentFlag] = useState<Partial<FeatureState>>(
    () => {
      const sourceFlag = identityFlag || propsEnvironmentFlag
      return sourceFlag ? _.cloneDeep(sourceFlag) : {}
    },
  )
  const [_externalResources, _setExternalResources] = useState<any[]>([])
  const [featureContentType, setFeatureContentType] = useState<
    Record<string, any>
  >({})
  const [featureLimitAlert, setFeatureLimitAlert] = useState({ percentage: 0 })
  const [githubId, setGithubId] = useState('')
  const [hasIntegrationWithGithub, setHasIntegrationWithGithub] =
    useState(false)
  const [hasMetadataRequired, setHasMetadataRequired] = useState(false)
  const [_isLoading, setIsLoading] = useState(false)
  const [_period, _setPeriod] = useState(30)
  const [projectFlag, setProjectFlag] = useState<Partial<ProjectFlag>>(() => {
    return propsProjectFlag
      ? _.cloneDeep(propsProjectFlag)
      : {
          description: undefined,
          is_archived: undefined,
          is_server_key_only: undefined,
          metadata: [],
          multivariate_options: [],
          name: undefined,
          tags: [],
        }
  })
  const [_scheduledChangeRequests, setScheduledChangeRequests] = useState<
    ChangeRequestSummary[]
  >([])
  const [segmentsChanged, setSegmentsChanged] = useState(false)
  const [selectedIdentity, setSelectedIdentity] =
    useState<SelectedIdentity | null>(null)
  const [settingsChanged, setSettingsChanged] = useState(false)
  const [showCreateSegment, setShowCreateSegment] = useState(false)
  const [skipSaveProjectFeature, setSkipSaveProjectFeature] = useState(false)
  const [valueChanged, setValueChanged] = useState(false)
  const [_error, setError] = useState<any>()
  const [userOverrides, setUserOverrides] = useState<UserOverrideType[]>()
  const [userOverridesError, setUserOverridesErrorState] = useState(false)
  const [userOverridesNoPermission, setUserOverridesNoPermissionState] =
    useState(false)
  const [userOverridesPaging, setUserOverridesPaging] = useState<{
    count: number
    currentPage: number
    next: string | null
  }>()
  const [enabledIndentity, setEnabledIndentity] = useState(false)

  const focusTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const close = useCallback(() => {
    closeModal()
  }, [])

  const onClosing = useCallback((): Promise<boolean> => {
    if (isEdit) {
      return new Promise((resolve) => {
        const projectFlagChanged = settingsChanged
        const environmentFlagChanged = valueChanged
        const segmentOverridesChanged = segmentsChanged
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
  }, [isEdit, settingsChanged, valueChanged, segmentsChanged])

  const setUserOverridesErrorFn = useCallback(() => {
    setUserOverrides([])
    setUserOverridesErrorState(true)
    setUserOverridesNoPermissionState(false)
    setUserOverridesPaging({ count: 0, currentPage: 1, next: null })
  }, [])

  const setUserOverridesNoPermissionFn = useCallback(() => {
    setUserOverrides([])
    setUserOverridesErrorState(false)
    setUserOverridesNoPermissionState(true)
    setUserOverridesPaging({ count: 0, currentPage: 1, next: null })
  }, [])

  const userOverridesPage = useCallback(
    (page: number, forceRefetch?: boolean) => {
      if (Utils.getIsEdge()) {
        // Early return if tab should be hidden
        if (Utils.getShouldHideIdentityOverridesTab(ProjectStore.model)) {
          setUserOverrides([])
          setUserOverridesPaging({
            count: 0,
            currentPage: 1,
            next: null,
          })
          return
        }

        getPermission(
          getStore(),
          {
            id: environmentId,
            level: 'environment',
            permissions: 'VIEW_IDENTITIES',
          },
          { forceRefetch },
        )
          .then((permissions: Record<string, boolean>) => {
            const hasViewIdentitiesPermission =
              permissions[Utils.getViewIdentitiesPermission()] ||
              permissions.ADMIN
            // Early return if user doesn't have permission
            if (!hasViewIdentitiesPermission) {
              setUserOverridesNoPermissionFn()
              return
            }

            data
              .get(
                `${Project.api}environments/${environmentId}/edge-identity-overrides?feature=${propsProjectFlag?.id}&page=${page}`,
              )
              .then(
                (res: {
                  results: Array<{
                    feature_state: FeatureState
                    identity_uuid: string
                    identifier: string
                  }>
                  count: number
                  next: string | null
                }) => {
                  setUserOverrides(
                    res.results.map((v) => ({
                      ...v.feature_state,
                      identity: {
                        id: v.identity_uuid,
                        identifier: v.identifier,
                      },
                    })),
                  )
                  setUserOverridesErrorState(false)
                  setUserOverridesNoPermissionState(false)
                  setUserOverridesPaging({
                    count: res.count,
                    currentPage: page,
                    next: res.next,
                  })
                },
              )
              .catch((response: { status?: number }) => {
                if (response?.status === 403) {
                  setUserOverridesNoPermissionFn()
                } else {
                  setUserOverridesErrorFn()
                }
              })
          })
          .catch(() => {
            setUserOverridesErrorFn()
          })

        return
      }

      data
        .get(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getFeatureStatesEndpoint()}/?anyIdentity=1&feature=${
            propsProjectFlag?.id
          }&page=${page}`,
        )
        .then(
          (res: {
            results: FeatureState[]
            count: number
            next: string | null
          }) => {
            setUserOverrides(res.results as UserOverrideType[])
            setUserOverridesErrorState(false)
            setUserOverridesNoPermissionState(false)
            setUserOverridesPaging({
              count: res.count,
              currentPage: page,
              next: res.next,
            })
          },
        )
        .catch((response: { status?: number }) => {
          if (response?.status === 403) {
            setUserOverridesNoPermissionFn()
          } else {
            setUserOverridesErrorFn()
          }
        })
    },
    [
      environmentId,
      propsProjectFlag?.id,
      setUserOverridesErrorFn,
      setUserOverridesNoPermissionFn,
    ],
  )

  const fetchChangeRequests = useCallback(
    (forceRefetch?: boolean) => {
      if (!propsProjectFlag?.id) return

      getChangeRequests(
        getStore(),
        {
          committed: false,
          environmentId,
          feature_id: propsProjectFlag?.id,
        },
        { forceRefetch },
      ).then((res) => {
        setChangeRequests(res.data?.results)
      })
    },
    [environmentId, propsProjectFlag?.id],
  )

  const fetchScheduledChangeRequests = useCallback(
    (forceRefetch?: boolean) => {
      if (!propsProjectFlag?.id) return

      const date = moment().toISOString()

      getChangeRequests(
        getStore(),
        {
          environmentId,
          feature_id: propsProjectFlag.id,
          live_from_after: date,
        },
        { forceRefetch },
      ).then((res) => {
        setScheduledChangeRequests(res.data?.results)
      })
    },
    [environmentId, propsProjectFlag?.id],
  )

  // Initial data load - intentionally runs only on mount
  useEffect(() => {
    if (propsProjectFlag) {
      userOverridesPage(1, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Component mount effects
  useEffect(() => {
    setInterceptClose(onClosing)

    if (Utils.getPlansPermission('METADATA')) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const contentType = Utils.getContentType(res.data, 'model', 'feature')
        setFeatureContentType(contentType)
      })
    }

    fetchChangeRequests()
    fetchScheduledChangeRequests()

    getGithubIntegration(getStore(), {
      organisation_id: AccountStore.getOrganisation().id,
    }).then((res) => {
      setGithubId(res?.data?.results[0]?.id)
      setHasIntegrationWithGithub(!!res?.data?.results?.length)
    })

    const timeoutRef = focusTimeoutRef.current
    return () => {
      if (timeoutRef) {
        clearTimeout(timeoutRef)
      }
    }
  }, [fetchChangeRequests, fetchScheduledChangeRequests, onClosing])

  // Update environmentFlag when props change
  useEffect(() => {
    const environmentFlagSource = identityFlag || propsEnvironmentFlag
    if (
      environmentFlagSource?.updated_at &&
      environmentFlag.updated_at &&
      environmentFlagSource.updated_at !== environmentFlag.updated_at
    ) {
      setEnvironmentFlag(_.cloneDeep(environmentFlagSource))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [identityFlag, propsEnvironmentFlag])

  // Update projectFlag when props change
  useEffect(() => {
    if (
      propsProjectFlag?.updated_at &&
      projectFlag.updated_at &&
      propsProjectFlag.updated_at !== projectFlag.updated_at
    ) {
      setProjectFlag(_.cloneDeep(propsProjectFlag))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propsProjectFlag])

  // Update multivariate options when environmentVariations change
  useEffect(() => {
    if (!identity && environmentVariations?.length) {
      setProjectFlag((prev) => ({
        ...prev,
        multivariate_options: prev.multivariate_options?.map((v) => {
          const matchingVariation = environmentVariations?.find(
            (e) => e.multivariate_feature_option === v.id,
          )
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
  }, [identity, environmentVariations])

  const renderUserOverridesNoResults = useCallback(() => {
    if (userOverridesError) {
      return (
        <div className='text-center py-4'>
          Failed to load identity overrides.
        </div>
      )
    }
    if (userOverridesNoPermission) {
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
  }, [userOverridesError, userOverridesNoPermission])

  const cleanInputValue = useCallback(
    (value: FlagsmithValue): FlagsmithValue => {
      if (value && typeof value === 'string') {
        return value.trim()
      }
      return value
    },
    [],
  )

  const save = useCallback(
    (func: (...args: any[]) => void, isSaving?: boolean) => {
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
              enabled: environmentFlag.enabled,
              feature_state_value: hasMultivariate
                ? propsEnvironmentFlag.feature_state_value
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
              initial_value: cleanInputValue(
                environmentFlag.feature_state_value,
              ),
              is_archived: projectFlag.is_archived,
              is_server_key_only: projectFlag.is_server_key_only,
              metadata:
                !propsProjectFlag?.metadata ||
                (propsProjectFlag.metadata !== projectFlag.metadata &&
                  projectFlag.metadata?.length)
                  ? projectFlag.metadata
                  : propsProjectFlag.metadata,
              multivariate_options: projectFlag.multivariate_options,
              name: projectFlag.name,
              tags: projectFlag.tags,
            },
            {
              skipSaveProjectFeature,
              ...propsProjectFlag,
            },
            {
              ...propsEnvironmentFlag,
              multivariate_feature_state_values:
                environmentVariations ||
                propsEnvironmentFlag?.multivariate_feature_state_values,
            },
            segmentOverrides,
          )
      }
    },
    [
      propsEnvironmentFlag,
      environmentId,
      identity,
      identityFlag,
      environmentFlag,
      projectFlag,
      propsProjectFlag,
      projectId,
      skipSaveProjectFeature,
      environmentVariations,
      segmentOverrides,
      cleanInputValue,
    ],
  )

  const changeSegment = useCallback(
    (items: FeatureState[]) => {
      items.forEach((item) => {
        item.enabled = enabledSegment
      })
      updateSegments(items)
      setEnabledSegment(!enabledSegment)
    },
    [enabledSegment, updateSegments],
  )

  const changeIdentity = useCallback(
    (items: UserOverrideType[]) => {
      Promise.all(
        items.map(
          (item) =>
            new Promise<void>((resolve) => {
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
        userOverridesPage(1)
      })

      setEnabledIndentity(!enabledIndentity)
    },
    [enabledIndentity, environmentId, userOverridesPage],
  )

  const toggleUserFlag = useCallback(
    ({
      enabled,
      id,
      identity: flagIdentity,
    }: {
      enabled: boolean
      id: number
      identity: { id: string; identifier: string }
    }) => {
      AppActions.changeUserFlag({
        environmentId,
        identity: flagIdentity.id,
        identityFlag: id,
        onSuccess: () => {
          userOverridesPage(1)
        },
        payload: {
          enabled: !enabled,
          id: flagIdentity.id,
          value: flagIdentity.identifier,
        },
      })
    },
    [environmentId, userOverridesPage],
  )

  const parseError = useCallback(
    (err: any): { featureError: string; featureWarning: string } => {
      let featureError = err?.message || err?.name?.[0] || err
      let featureWarning = ''
      //Treat multivariate no changes as warnings
      if (
        featureError?.includes?.('no changes') &&
        propsProjectFlag?.multivariate_options?.length
      ) {
        featureWarning = `Your feature contains no changes to its value, enabled state or environment weights. If you have adjusted any variation values this will have been saved for all environments.`
        featureError = ''
      }
      return { featureError, featureWarning }
    },
    [propsProjectFlag?.multivariate_options?.length],
  )

  const addItem = useCallback(() => {
    setIsLoading(true)
    const selectedIdentityValue = selectedIdentity?.value
    const identities = identity ? identity : []

    if (
      selectedIdentityValue &&
      !_.find(identities, (v: string) => v === selectedIdentityValue)
    ) {
      data
        .post(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${selectedIdentityValue}/${Utils.getFeatureStatesEndpoint()}/`,
          {
            enabled: !propsEnvironmentFlag?.enabled,
            feature: propsProjectFlag?.id,
            feature_state_value:
              propsEnvironmentFlag?.feature_state_value || null,
          },
        )
        .then(() => {
          setIsLoading(false)
          setSelectedIdentity(null)
          userOverridesPage(1)
        })
        .catch((e: any) => {
          setError(e)
          setIsLoading(false)
        })
    } else {
      setIsLoading(false)
      setSelectedIdentity(null)
    }
  }, [
    selectedIdentity,
    identity,
    environmentId,
    propsEnvironmentFlag,
    propsProjectFlag?.id,
    userOverridesPage,
  ])

  // Derived values
  const environment = ProjectStore.getEnvironment(environmentId)
  const isVersioned = !!environment?.use_v2_feature_versioning
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)
  const project = ProjectStore.model as ProjectType
  const caseSensitive = project?.only_allow_lower_case_feature_names
  const regex = project?.feature_name_regex
  const controlValue = Utils.calculateControl(projectFlag.multivariate_options)
  const invalid =
    !!projectFlag.multivariate_options &&
    projectFlag.multivariate_options.length &&
    controlValue < 0
  const isVersionedChangeRequest = existingChangeRequest && isVersioned
  const hideIdentityOverridesTab = Utils.getShouldHideIdentityOverridesTab()
  const isCodeReferencesEnabled = Utils.getFlagsmithHasFeature(
    'git_code_references',
  )

  let regexValid = true
  try {
    if (!isEdit && projectFlag.name && regex) {
      regexValid = !!projectFlag.name.match(new RegExp(regex))
    }
  } catch (e) {
    regexValid = false
  }

  // Permission hooks
  const { permission: createFeature } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'CREATE_FEATURE',
  })

  const { permission: projectAdmin } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'ADMIN',
  })

  const { permission: manageSegmentOverrides } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: 'MANAGE_SEGMENT_OVERRIDES',
  })

  const { permission: viewIdentities } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: 'VIEW_IDENTITIES',
  })

  // Dynamic permission for managing features (depends on is4Eyes and identity)
  const manageFeaturePermission = Utils.getManageFeaturePermission(
    is4Eyes,
    identity,
  )
  const { permission: savePermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: manageFeaturePermission,
    tags: projectFlag.tags,
  })

  // Update skipSaveProjectFeature based on permission
  useEffect(() => {
    if (skipSaveProjectFeature !== !createFeature) {
      setSkipSaveProjectFeature(!createFeature)
    }
  }, [createFeature, skipSaveProjectFeature])

  const Provider = identity ? IdentityProvider : FeatureListProvider

  return (
    <ProjectProvider id={projectId}>
      {({ project: proj }) => (
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
            {
              error: providerError,
              isSaving,
            }: { error: any; isSaving: boolean },
            {
              createChangeRequest,
              createFlag,
              editFeatureSegments,
              editFeatureSettings,
              editFeatureValue,
            }: {
              createChangeRequest: (...args: any[]) => void
              createFlag: (...args: any[]) => void
              editFeatureSegments: (...args: any[]) => void
              editFeatureSettings: (...args: any[]) => void
              editFeatureValue: (...args: any[]) => void
            },
          ) => {
            const saveFeatureValue = saveFeatureWithValidation(
              (schedule: boolean) => {
                if ((is4Eyes || schedule) && !identity) {
                  setSegmentsChanged(false)
                  setValueChanged(false)
                  // Until this page and feature-list-store are refactored, this is the best way of parsing feature states
                  const featureStates = (segmentOverrides || [])
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
                      Object.assign({}, propsEnvironmentFlag, {
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
                      featureStates={featureStates}
                      onSave={({
                        approvals,
                        description,
                        ignore_conflicts,
                        live_from,
                        title,
                      }: {
                        approvals: any[]
                        description: string
                        ignore_conflicts: boolean
                        live_from: string
                        title: string
                      }) => {
                        closeModal2()
                        save(
                          (
                            pId: number,
                            envId: string,
                            flag: any,
                            pFlag: ProjectFlag,
                            envFlag: FeatureState,
                            segOverrides: FeatureState[],
                          ) => {
                            createChangeRequest(
                              pId,
                              envId,
                              flag,
                              pFlag,
                              envFlag,
                              segOverrides,
                              {
                                approvals,
                                description,
                                featureStateId:
                                  existingChangeRequest &&
                                  existingChangeRequest.feature_states?.[0]?.id,
                                id:
                                  existingChangeRequest &&
                                  existingChangeRequest.id,
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
              (schedule: boolean) => {
                setSegmentsChanged(false)

                if ((is4Eyes || schedule) && isVersioned && !identity) {
                  return saveFeatureValue()
                } else {
                  save(editFeatureSegments, isSaving)
                }
              },
            )

            const onCreateFeature = saveFeatureWithValidation(() => {
              save(createFlag, isSaving)
            })
            const isLimitReached = false

            const { featureError, featureWarning } = parseError(providerError)

            const _hasMetadataRequired =
              hasMetadataRequired && !projectFlag.metadata?.length

            return (
              <div id='create-feature-modal'>
                {isEdit && !identity ? (
                  <>
                    <FeaturePipelineStatus
                      projectId={projectId}
                      featureId={projectFlag?.id}
                    />
                    <Tabs urlParam='tab' history={history} overflowX>
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
                          error={providerError}
                          createFeature={createFeature}
                          hideValue={false}
                          isEdit={isEdit}
                          noPermissions={noPermissions}
                          featureState={environmentFlag as FeatureState}
                          projectFlag={projectFlag as ProjectFlag}
                          onEnvironmentFlagChange={(changes) => {
                            setEnvironmentFlag((prev) => ({
                              ...prev,
                              ...changes,
                            }))
                            setValueChanged(true)
                          }}
                          onProjectFlagChange={(changes) => {
                            setProjectFlag((prev) => ({
                              ...prev,
                              ...changes,
                            }))
                          }}
                          onRemoveMultivariateOption={removeMultivariateOption}
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
                          json={propsEnvironmentFlag}
                        />
                        <FlagValueFooter
                          is4Eyes={is4Eyes}
                          isVersioned={isVersioned}
                          projectId={projectId}
                          projectFlag={projectFlag as ProjectFlag}
                          environmentId={environmentId}
                          environmentName={
                            _.find(proj.environments, {
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
                      {(!existingChangeRequest || isVersionedChangeRequest) && (
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
                          <FormGroup className='mb-4'>
                            <FeatureInPipelineGuard
                              projectId={projectId}
                              featureId={projectFlag?.id}
                              renderFallback={(matchingReleasePipeline: {
                                name: string
                              }) => (
                                <>
                                  <h5 className='mb-2'>Segment Overrides </h5>
                                  <InfoMessage
                                    title={`Feature in release pipeline`}
                                  >
                                    This feature is in{' '}
                                    <b>{matchingReleasePipeline?.name}</b>{' '}
                                    release pipeline and no segment overrides
                                    can be created
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
                                  {!showCreateSegment &&
                                    !!manageSegmentOverrides &&
                                    !disableCreate && (
                                      <div className='text-right'>
                                        <Button
                                          size='small'
                                          onClick={() => {
                                            setShowCreateSegment(true)
                                          }}
                                          theme='outline'
                                          disabled={!!isLimitReached}
                                        >
                                          Create Feature-Specific Segment
                                        </Button>
                                      </div>
                                    )}
                                  {!showCreateSegment && !noPermissions && (
                                    <Button
                                      onClick={() =>
                                        changeSegment(segmentOverrides || [])
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
                                {segmentOverrides ? (
                                  <>
                                    <ErrorMessage error={featureError} />
                                    <WarningMessage
                                      warningMessage={featureWarning}
                                    />
                                    <SegmentOverrides
                                      setShowCreateSegment={
                                        setShowCreateSegment
                                      }
                                      readOnly={!manageSegmentOverrides}
                                      is4Eyes={is4Eyes}
                                      showEditSegment
                                      showCreateSegment={showCreateSegment}
                                      feature={projectFlag.id}
                                      projectId={projectId}
                                      multivariateOptions={
                                        projectFlag.multivariate_options
                                      }
                                      environmentId={environmentId}
                                      value={segmentOverrides}
                                      controlValue={
                                        environmentFlag.feature_state_value
                                      }
                                      onChange={(v: FeatureState[]) => {
                                        setSegmentsChanged(true)
                                        updateSegments(v)
                                      }}
                                      highlightSegmentId={highlightSegmentId}
                                    />
                                  </>
                                ) : (
                                  <div className='text-center'>
                                    <Loader />
                                  </div>
                                )}
                                {!showCreateSegment && (
                                  <ModalHR className='mt-4' />
                                )}
                                {!showCreateSegment && (
                                  <div>
                                    <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                                      {is4Eyes && isVersioned
                                        ? 'This will create a change request with any value and segment override changes for the environment'
                                        : 'This will update the segment overrides for the environment'}{' '}
                                      <strong>
                                        {
                                          _.find(proj.environments, {
                                            api_key: environmentId,
                                          })?.name
                                        }
                                      </strong>
                                    </p>
                                    <div className='text-right'>
                                      {(() => {
                                        const getButtonText = () => {
                                          if (isSaving) {
                                            return existingChangeRequest
                                              ? 'Updating Change Request'
                                              : 'Creating Change Request'
                                          }
                                          return existingChangeRequest
                                            ? 'Update Change Request'
                                            : 'Create Change Request'
                                        }

                                        const getScheduleButtonText = () => {
                                          if (isSaving) {
                                            return existingChangeRequest
                                              ? 'Updating Change Request'
                                              : 'Scheduling Update'
                                          }
                                          return existingChangeRequest
                                            ? 'Update Change Request'
                                            : 'Schedule Update'
                                        }

                                        if (isVersioned && is4Eyes) {
                                          return Utils.renderWithPermission(
                                            savePermission,
                                            Utils.getManageFeaturePermissionDescription(
                                              is4Eyes,
                                              identity,
                                            ),
                                            <Button
                                              onClick={() =>
                                                saveFeatureSegments(false)
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
                                          manageSegmentOverrides,
                                          Constants.environmentPermissions(
                                            'Manage segment overrides',
                                          ),
                                          <>
                                            {!is4Eyes && isVersioned && (
                                              <>
                                                <Button
                                                  feature='SCHEDULE_FLAGS'
                                                  theme='secondary'
                                                  onClick={() =>
                                                    saveFeatureSegments(true)
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
                                                saveFeatureSegments(false)
                                              }
                                              type='button'
                                              data-test='update-feature-segments-btn'
                                              id='update-feature-segments-btn'
                                              disabled={
                                                isSaving ||
                                                !projectFlag.name ||
                                                invalid ||
                                                !manageSegmentOverrides
                                              }
                                            >
                                              {isSaving
                                                ? 'Updating'
                                                : 'Update Segment Overrides'}
                                            </Button>
                                          </>,
                                        )
                                      })()}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </FeatureInPipelineGuard>
                          </FormGroup>
                        </TabItem>
                      )}
                      {!existingChangeRequest && !hideIdentityOverridesTab && (
                        <TabItem
                          data-test='identity_overrides'
                          tabLabel='Identity Overrides'
                        >
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
                                          collapseId={'identity-overrides'}
                                        >
                                          Identity overrides override feature
                                          values for individual identities. The
                                          overrides take priority over an
                                          segment overrides and environment
                                          defaults. Identity overrides will only
                                          apply when you identify via the SDK.{' '}
                                          <a
                                            target='_blank'
                                            href='https://docs.flagsmith.com/basic-features/managing-identities'
                                            rel='noreferrer'
                                          >
                                            Check the Docs for more details
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
                                          changeIdentity(userOverrides || [])
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
                                  items={userOverrides}
                                  paging={userOverridesPaging}
                                  renderSearchWithNoResults
                                  nextPage={() =>
                                    userOverridesPage(
                                      (userOverridesPaging?.currentPage || 0) +
                                        1,
                                    )
                                  }
                                  prevPage={() =>
                                    userOverridesPage(
                                      (userOverridesPaging?.currentPage || 2) -
                                        1,
                                    )
                                  }
                                  goToPage={(page: number) =>
                                    userOverridesPage(page)
                                  }
                                  searchPanel={
                                    !Utils.getIsEdge() && (
                                      <div className='text-center mt-2 mb-2'>
                                        <Flex className='text-left'>
                                          <IdentitySelect
                                            isEdge={false}
                                            ignoreIds={userOverrides?.map(
                                              (v) => v.identity?.id,
                                            )}
                                            environmentId={environmentId}
                                            data-test='select-identity'
                                            placeholder='Create an Identity Override...'
                                            value={selectedIdentity}
                                            onChange={(
                                              si: SelectedIdentity,
                                            ) => {
                                              setSelectedIdentity(si)
                                              // Call addItem after state update
                                              setTimeout(() => addItem(), 0)
                                            }}
                                          />
                                        </Flex>
                                      </div>
                                    )
                                  }
                                  renderRow={(
                                    identityFlag: UserOverrideType,
                                  ) => {
                                    const {
                                      enabled,
                                      feature_state_value,
                                      id,
                                      identity: flagIdentity,
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
                                                toggleUserFlag({
                                                  enabled,
                                                  id,
                                                  identity: flagIdentity,
                                                })
                                              }
                                              disabled={Utils.getIsEdge()}
                                            />
                                          </div>
                                          <div className='font-weight-medium fs-small lh-sm'>
                                            {flagIdentity.identifier}
                                          </div>
                                        </Row>
                                        <Row>
                                          <div
                                            className='table-column'
                                            style={{
                                              width: '188px',
                                            }}
                                          >
                                            {feature_state_value !== null && (
                                              <FeatureValue
                                                value={feature_state_value}
                                              />
                                            )}
                                          </div>
                                          <div className='table-column'>
                                            <Button
                                              target='_blank'
                                              href={`/project/${projectId}/environment/${environmentId}/users/${flagIdentity.identifier}/${flagIdentity.id}?flag=${projectFlag.name}`}
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
                                              onClick={(
                                                e: React.MouseEvent,
                                              ) => {
                                                e.stopPropagation()
                                                removeUserOverride({
                                                  cb: () =>
                                                    userOverridesPage(1, true),
                                                  environmentId,
                                                  identifier:
                                                    flagIdentity.identifier,
                                                  identity: flagIdentity.id,
                                                  identityFlag,
                                                  projectFlag:
                                                    projectFlag as ProjectFlag,
                                                })
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
                                  renderNoResults={renderUserOverridesNoResults()}
                                  isLoading={!userOverrides}
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
                      )}
                      {!Project.disableAnalytics && (
                        <TabItem tabLabel={'Analytics'}>
                          <div className='mb-4'>
                            <FeatureAnalytics
                              projectId={`${proj.id}`}
                              featureId={`${projectFlag.id}`}
                              defaultEnvironmentIds={[`${environment?.id}`]}
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
                                {hasUnhealthyEvents && (
                                  <IonIcon
                                    icon={warning}
                                    style={{
                                      color:
                                        Constants.featureHealth.unhealthyColor,
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
                            environmentId={environmentId}
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
                            projectId={projectId}
                          />
                        </TabItem>
                      )}
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
                            organisationId={AccountStore.getOrganisation().id}
                            featureId={projectFlag.id}
                            projectId={`${projectId}`}
                            environmentId={environmentId}
                          />
                        </TabItem>
                      )}
                      {!existingChangeRequest && flagId && isVersioned && (
                        <TabItem data-test='change-history' tabLabel='History'>
                          <FeatureHistory
                            feature={projectFlag.id}
                            projectId={`${projectId}`}
                            environmentId={environment?.id}
                            environmentApiKey={environment?.api_key}
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
                            projectAdmin={projectAdmin}
                            createFeature={createFeature}
                            featureContentType={featureContentType}
                            identity={identity}
                            isEdit={isEdit}
                            projectId={projectId}
                            projectFlag={projectFlag as ProjectFlag}
                            onChange={(changes) => {
                              // Update projectFlag with changes
                              setProjectFlag((prev) => ({
                                ...prev,
                                ...changes,
                              }))

                              // Set settingsChanged flag unless it's only metadata changing
                              if ((changes as any).metadata === undefined) {
                                setSettingsChanged(true)
                              }
                            }}
                            onHasMetadataRequiredChange={setHasMetadataRequired}
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
                                      _hasMetadataRequired
                                    }
                                  >
                                    {isSaving ? 'Updating' : 'Update Settings'}
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
                  <CreateFeatureView
                    projectId={projectId}
                    projectFlag={projectFlag}
                    environmentFlag={environmentFlag}
                    identityFlag={identityFlag}
                    featureContentType={featureContentType}
                    identity={identity}
                    isEdit={isEdit}
                    isSaving={isSaving}
                    invalid={invalid}
                    regexValid={regexValid}
                    caseSensitive={caseSensitive}
                    regex={regex}
                    featureLimitPercentage={featureLimitAlert.percentage}
                    hasMetadataRequired={_hasMetadataRequired}
                    providerError={providerError}
                    onProjectFlagChange={(changes) => {
                      setProjectFlag((prev) => ({
                        ...prev,
                        ...changes,
                      }))
                    }}
                    onEnvironmentFlagChange={(changes) => {
                      setEnvironmentFlag((prev) => ({
                        ...prev,
                        ...changes,
                      }))
                      setValueChanged(true)
                    }}
                    onRemoveMultivariateOption={removeMultivariateOption}
                    onHasMetadataRequiredChange={setHasMetadataRequired}
                    onCreateFeature={onCreateFeature}
                    parseError={parseError}
                  />
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
                              _.find(proj.environments, {
                                api_key: environmentId,
                              })?.name
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
                            disabled={isSaving || !projectFlag.name || invalid}
                          >
                            {isSaving ? 'Updating' : 'Update Feature'}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          }}
        </Provider>
      )}
    </ProjectProvider>
  )
}

CreateFeatureModal.displayName = 'CreateFeatureModal'
