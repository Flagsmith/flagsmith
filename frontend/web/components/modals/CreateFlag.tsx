import React, { FC, useCallback, useEffect, useMemo, useState } from 'react'
import {
  ChangeRequestSummary,
  FeatureState,
  MultivariateFeatureStateValue,
  MultivariateOption,
  ProjectFlag,
  SegmentOverride,
} from 'common/types/responses'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import Utils from 'common/utils/utils'
import { useHasPermission } from 'common/providers/Permission'
import cloneDeep from 'lodash/cloneDeep'
import CreateFlagValue, {
  CreateFeatureStateType,
  CreateProjectFlagType,
} from './CreateFlagValue'
import FeatureLimit from 'components/FeatureLimit'
import ConfigProvider from 'common/providers/ConfigProvider'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import FeatureProvider from 'common/providers/FeatureProvider'
import { setInterceptClose } from './base/ModalDefault'
import SegmentOverrides from 'components/SegmentOverrides'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'
import { useGetProjectQuery } from 'common/services/useProject'
import IdentityProvider from 'common/providers/IdentityProvider'
import FeatureListProvider from 'common/providers/FeatureListProvider'
const Project = require('common/project')
import AppActions from 'common/dispatcher/app-actions'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import FeatureUsage from 'components/FeatureUsage'
import CreateFlagSettings from './CreateFlagSettings'
import useRegexValid from 'common/useRegexValid'
import FeatureListStore from 'common/stores/feature-list-store'
type CreateFlagType = {
  environmentApiKey: string
  projectId: string
  changeRequest?: ChangeRequestSummary
  identity?: string
  projectFlag: ProjectFlag
  // Passed when viewing a change request
  multivariate_options?: MultivariateOption[] | null
  environmentVariations: MultivariateFeatureStateValue[] | null
  history: History
  featureState?: FeatureState
  segmentOverrides: SegmentOverride[]
  updateSegments: (newValue: SegmentOverride[]) => void
}

const _CreateFlag: FC<CreateFlagType> = ({
  changeRequest,
  environmentApiKey,
  environmentVariations,
  featureState: previousFeatureState,
  history,
  identity,
  multivariate_options,
  projectFlag: previousProjectFlag,
  projectId,
  segmentOverrides,
  updateSegments,
}) => {
  const { data: project } = useGetProjectQuery({ id: projectId })
  const { data: environments } = useGetEnvironmentsQuery({ projectId })
  const environment = environments?.results?.find(
    (env) => env.api_key === environmentApiKey,
  )
  const [killSwitch, setKillSwitch] = useState(false)
  const [_, setUpdate] = useState(Date.now())
  const [valueChanged, setValueChanged] = useState(false)
  const [segmentsChanged, setSegmentsChanged] = useState(false)
  const [settingsChanged, setSettingsChanged] = useState(false)
  const [showCreateSegment, setShowCreateSegment] = useState(false)

  const [projectFlag, setProjectFlag] = useState<CreateProjectFlagType>(
    previousProjectFlag
      ? cloneDeep(previousProjectFlag)
      : {
          default_enabled: false,
          description: '',
          initial_value: '',
          is_archived: false,
          is_server_key_only: false,
          multivariate_options: [],
          name: '',
          num_identity_overrides: 0,
          num_segment_overrides: 0,
          owner_groups: [],
          owners: [],
          project: parseInt(projectId),
          tags: [],
          type: 'STANDARD',
        },
  )
  const isEdit = !!projectFlag?.id
  const regexValid = useRegexValid(
    projectFlag.name,
    project?.feature_name_regex || '',
  )

  const controlValuePercentage = Utils.calculateControl(multivariate_options)
  const invalidFeature = !projectFlag.name
  const invalidMultivariate =
    !!multivariate_options &&
    multivariate_options.length &&
    controlValuePercentage < 0

  const onClosing = useCallback(() => {
    if (isEdit) {
      return new Promise((resolve) => {
        if (valueChanged || segmentsChanged || settingsChanged) {
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
  }, [valueChanged, isEdit, segmentsChanged, settingsChanged])

  useEffect(() => {
    setInterceptClose(onClosing)
  }, [onClosing])

  const [featureState, setFeatureState] = useState<CreateFeatureStateType>(
    previousFeatureState
      ? cloneDeep(previousFeatureState)
      : {
          enabled: false,
          feature_state_value: '',
          multivariate_feature_state_values: [],
        },
  )

  const { isLoading: projectPermissionLoading, permission: isProjectAdmin } =
    useHasPermission({
      id: `${projectId || ''}`,
      level: 'project',
      permission: 'ADMIN',
    })
  const { isLoading: manageFeaturesLoading, permission: canManageFeatures } =
    useHasPermission({
      id: `${environmentApiKey || ''}`,
      level: 'environment',
      permission: Utils.getManageFeaturePermission(
        Utils.changeRequestsEnabled(
          environment?.minimum_change_request_approvals,
        ),
      ),
    })

  const {
    isLoading: manageSegmentsLoading,
    permission: canManageSegmentOverrides,
  } = useHasPermission({
    id: `${environmentApiKey || ''}`,
    level: 'environment',
    permission: 'MANAGE_SEGMENT_OVERRIDES',
  })

  const hideIdentityOverridesTab =
    !!changeRequest || Utils.getShouldHideIdentityOverridesTab(project)
  const hideAnalyticsTab = Project.disableAnalytics
  const updateTab = () => setUpdate(Date.now())

  const saveData = useMemo(() => {
    const skipSaveProjectFeature = !isProjectAdmin
    return {
      environmentFlag: identity ? previousFeatureState : featureState,
      identityFlag: identity ? featureState : undefined,
      projectFlag: {
        ...projectFlag,
        skipSaveProjectFeature,
      },
      segmentOverrides,
    }
  }, [
    identity,
    projectFlag,
    featureState,
    previousFeatureState,
    isProjectAdmin,
    segmentOverrides,
  ])

  const toggleAllSegmentOverrides = () => {
    updateSegments(
      segmentOverrides?.map((v) => ({
        ...v,
        enabled: killSwitch,
      })),
    )
    setKillSwitch(!killSwitch)
  }

  const close = () => {
    closeModal()
  }
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)

  if (!project || !environment)
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  const permissionsLoading =
    manageSegmentsLoading || manageFeaturesLoading || projectPermissionLoading
  if (permissionsLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const is4EyesSegmentOverrides = false // todo: add versioned change requests
  const saveFeatureSegments = () => {
    setSegmentsChanged(false)
  }
  const Provider: typeof FeatureListProvider = (
    identity ? IdentityProvider : FeatureListProvider
  ) as any

  return (
    <Provider
      onSave={() => {
        if (identity) {
          close()
        }
        AppActions.refreshFeatures(projectId, environmentApiKey)
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
        const controlValue = Utils.calculateControl(
          featureState.multivariate_feature_state_values,
        )

        const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
          project.total_features,
          project.max_features_allowed,
        )
        const isOverLimit = featureLimitAlert.percentage >= 100
        const mvInvalid =
          !!multivariate_options &&
          multivariate_options.length &&
          controlValue < 0

        const onCreateFeature = () => {
          FeatureListStore.isSaving = true
          createFlag(
            projectId,
            environmentApiKey,
            {
              ...projectFlag,
              default_enabled: featureState.enabled,
              initial_value: featureState.feature_state_value,
            },
            [],
          )
        }
        const preventCreateFeature =
          isSaving ||
          mvInvalid ||
          !projectFlag.name ||
          isOverLimit ||
          !regexValid

        return isEdit ? (
          <div id='create-feature-modal'>
            <Tabs
              className='px-0'
              onChange={updateTab}
              history={history}
              urlParam='tab'
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
                <FeatureLimit project={project} />
                {!!identity && projectFlag.description}
                <CreateFlagValue
                  featureState={featureState}
                  setFeatureState={setFeatureState}
                  project={project}
                  environmentApiKey={environmentApiKey}
                  projectFlag={projectFlag}
                  setProjectFlag={(projectFlag) => {
                    setProjectFlag(projectFlag)
                    setValueChanged(true)
                  }}
                />
                <ModalHR className='mt-4' />
                <div className='text-right mt-4 mb-3 fs-small lh-sm modal-caption'>
                  {is4Eyes
                    ? 'This will create a change request for the environment'
                    : 'This will update the feature value for the environment'}{' '}
                  <strong>{environment.name}</strong>
                </div>
              </TabItem>
              {!changeRequest && (
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
                  <Row className='justify-content-between mb-2 segment-overrides-title'>
                    <Tooltip
                      title={
                        <h5 className='mb-0'>
                          Segment Overrides <Icon name='info-outlined' />
                        </h5>
                      }
                      place='top'
                    >
                      {Constants.strings.SEGMENT_OVERRIDES_DESCRIPTION}
                    </Tooltip>
                    {!showCreateSegment && !canManageSegmentOverrides && (
                      <Button
                        onClick={toggleAllSegmentOverrides}
                        type='button'
                        theme='secondary'
                        size='small'
                      >
                        {killSwitch ? 'Enable All' : 'Disable All'}
                      </Button>
                    )}
                  </Row>

                  <SegmentOverrides
                    readOnly={!canManageSegmentOverrides}
                    showEditSegment
                    showCreateSegment={showCreateSegment}
                    setShowCreateSegment={setShowCreateSegment}
                    feature={projectFlag.id}
                    projectId={projectId}
                    multivariateOptions={multivariate_options}
                    environmentId={environmentApiKey}
                    value={segmentOverrides}
                    controlValue={featureState.feature_state_value}
                    onChange={(v: SegmentOverride[]) => {
                      setSegmentsChanged(true)
                      editFeatureSegments(
                        projectId,
                        environmentApiKey,
                        projectFlag,
                        previousProjectFlag,
                        featureState,
                        segmentOverrides,
                      )
                    }}
                  />
                  {!showCreateSegment && (
                    <>
                      <ModalHR className='mt-4' />
                      <div>
                        <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                          {is4Eyes && is4EyesSegmentOverrides
                            ? 'This will create a change request for the environment'
                            : 'This will update the segment overrides for the environment'}{' '}
                          <strong>{environment.name}</strong>
                        </p>
                        <div className='text-right'>
                          {Utils.renderWithPermission(
                            canManageSegmentOverrides,
                            Constants.environmentPermissions(
                              'Manage segment overrides',
                            ),
                            <Button
                              onClick={saveFeatureSegments}
                              type='button'
                              data-test='update-feature-segments-btn'
                              id='update-feature-segments-btn'
                              disabled={
                                isSaving ||
                                invalidFeature ||
                                invalidMultivariate ||
                                !canManageSegmentOverrides
                              }
                            >
                              {isSaving
                                ? 'Updating'
                                : 'Update Segment Overrides'}
                            </Button>,
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </TabItem>
              )}
              {!hideIdentityOverridesTab && (
                <TabItem
                  data-test='identity_overrides'
                  tabLabel='Identity Overrides'
                >
                  <div />
                </TabItem>
              )}
              {!hideAnalyticsTab && !!projectFlag && (
                <TabItem data-test='analytics' tabLabel='Analytics'>
                  <FeatureUsage
                    featureId={projectFlag.id!}
                    projectId={projectFlag.project!}
                    environmentId={environment.id}
                  />
                </TabItem>
              )}
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
                <CreateFlagSettings
                  projectFlag={projectFlag}
                  setProjectFlag={(projectFlag) => {
                    setProjectFlag(projectFlag)
                    setSettingsChanged(true)
                  }}
                  project={project}
                />
              </TabItem>
            </Tabs>
          </div>
        ) : (
          <div className='px-3 mt-2 create-feature-tab'>
            <CreateFlagValue
              project={project}
              featureState={featureState}
              setFeatureState={setFeatureState}
              environmentApiKey={environmentApiKey}
              projectFlag={projectFlag}
              setProjectFlag={setProjectFlag}
            />
            <CreateFlagSettings
              projectFlag={projectFlag}
              setProjectFlag={setProjectFlag}
              project={project}
            />
            <ModalHR className={`my-4`} />
            <div className='text-right mb-3'>
              {project.prevent_flag_defaults ? (
                <p className='text-right modal-caption fs-small lh-sm'>
                  This will create the feature for{' '}
                  <strong>all environments</strong>, you can edit this feature
                  per environment once the feature's enabled state and
                  environment once the feature is created.
                </p>
              ) : (
                <p className='text-right modal-caption fs-small lh-sm'>
                  This will create the feature for{' '}
                  <strong>all environments</strong>, you can edit this feature
                  per environment once the feature is created.
                </p>
              )}

              <Button
                onClick={onCreateFeature}
                data-test='create-feature-btn'
                id='create-feature-btn'
                disabled={preventCreateFeature}
              >
                {isSaving ? 'Creating' : 'Create Feature'}
              </Button>
            </div>
          </div>
        )
      }}
    </Provider>
  )
}

export default FeatureProvider(
  ConfigProvider(withSegmentOverrides(_CreateFlag)),
)
