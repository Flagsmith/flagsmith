import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { useHasPermission } from 'common/providers/Permission'
import SegmentOverrides from 'components/SegmentOverrides'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import ModalHR from 'components/modals/ModalHR'
import FeatureInPipelineGuard from 'components/release-pipelines/FeatureInPipelineGuard'
import Utils from 'common/utils/utils'
import { ProjectFlag } from 'common/types/responses'
import { FeatureExperimentFreeze } from 'common/hooks/useFeatureExperimentFreeze'
import ExperimentFreezeNotice from 'components/modals/create-feature/components/ExperimentFreezeNotice'
import { EnvironmentPermission } from 'common/types/permissions.types'

export type SegmentOverrideValue = {
  enabled?: boolean
  [key: string]: unknown
}

type SegmentOverridesTabProps = {
  projectId: number
  environmentId: string
  projectFlag: ProjectFlag
  segmentOverrides?: SegmentOverrideValue[]
  updateSegments: (segments: SegmentOverrideValue[]) => void
  controlValue: string | number | boolean | null
  controlEnabled?: boolean
  onSegmentsChange: () => void
  saveFeatureSegments: (schedule: boolean) => void
  isSaving: boolean
  invalid: boolean
  error: any
  existingChangeRequest?: { id: number }
  noPermissions?: boolean
  freeze?: FeatureExperimentFreeze
  disableCreate?: boolean
  highlightSegmentId?: number
}

const SegmentOverridesTab: FC<SegmentOverridesTabProps> = ({
  controlEnabled,
  controlValue,
  disableCreate,
  environmentId,
  error,
  existingChangeRequest,
  freeze,
  highlightSegmentId,
  invalid,
  isSaving,
  noPermissions,
  onSegmentsChange,
  projectFlag,
  projectId,
  saveFeatureSegments,
  segmentOverrides,
  updateSegments,
}) => {
  const [showCreateSegment, setShowCreateSegment] = useState(false)
  const [enabledSegment, setEnabledSegment] = useState(false)
  const [isComparing, setIsComparing] = useState(false)

  const { getEnvironment } = useProjectEnvironments(projectId)
  const environment = getEnvironment(environmentId)
  const isVersioned = !!environment?.use_v2_feature_versioning
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)

  const { permission: manageSegmentOverrides } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
  })

  const { permission: savePermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getManageFeaturePermission(is4Eyes),
    tags: projectFlag.tags,
  })

  const changeSegment = (items: SegmentOverrideValue[]) => {
    items.forEach((item) => {
      item.enabled = enabledSegment
    })
    updateSegments(items)
    setEnabledSegment(!enabledSegment)
  }

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
    return existingChangeRequest ? 'Update Change Request' : 'Schedule Update'
  }

  const environmentName = environment?.name || ''

  let featureError =
    error?.metadata?.flatMap((m: any) => m.non_field_errors ?? []).join('\n') ||
    error?.message ||
    error?.name?.[0] ||
    error
  let featureWarning = ''
  if (
    featureError?.includes?.('no changes') &&
    projectFlag.multivariate_options?.length
  ) {
    featureWarning =
      'Your feature contains no changes to its value, enabled state or environment weights. If you have adjusted any variation values this will have been saved for all environments.'
    featureError = ''
  }

  return (
    <FormGroup className='mb-4'>
      <FeatureInPipelineGuard
        projectId={projectId}
        featureId={projectFlag?.id}
        renderFallback={(matchingReleasePipeline) => (
          <>
            <h5 className='mb-2'>Segment Overrides </h5>
            <InfoMessage title={`Feature in release pipeline`}>
              This feature is in <b>{matchingReleasePipeline?.name}</b> release
              pipeline and no segment overrides can be created
            </InfoMessage>
          </>
        )}
      >
        <div>
          <Row className='align-items-center mb-2 gap-4 segment-overrides-title'>
            {!isComparing && (
              <div className='flex-fill'>
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
              </div>
            )}
            {!isComparing &&
              !showCreateSegment &&
              manageSegmentOverrides &&
              !disableCreate &&
              !freeze?.isFrozen &&
              !freeze?.isLoading && (
                <div className='text-right'>
                  <Button
                    size='small'
                    onClick={() => {
                      setShowCreateSegment(true)
                    }}
                    theme='outline'
                  >
                    Create Feature-Specific Segment
                  </Button>
                </div>
              )}
            {!isComparing &&
              !showCreateSegment &&
              !noPermissions &&
              !freeze?.isFrozen &&
              !freeze?.isLoading && (
                <Button
                  onClick={() => changeSegment(segmentOverrides || [])}
                  type='button'
                  theme='secondary'
                  size='small'
                >
                  {enabledSegment ? 'Enable All' : 'Disable All'}
                </Button>
              )}
          </Row>
          {freeze?.isFrozen && freeze.experiment && (
            <ExperimentFreezeNotice
              experiment={freeze.experiment}
              projectId={projectId}
              environmentId={environmentId}
            />
          )}
          <div className='text-muted mb-2'>
            <p>
              Segment Overrides apply when the identity traits match the segment
              rules.
            </p>{' '}
            <p>
              Identity Overrides always override Segment Overrides.{' '}
              <a
                target='_blank'
                href='https://docs.flagsmith.com/basic-features/segments'
                rel='noreferrer'
              >
                Learn more
              </a>
            </p>
          </div>
          {segmentOverrides ? (
            <>
              <ErrorMessage error={featureError} />
              <WarningMessage warningMessage={featureWarning} />
              <SegmentOverrides
                setShowCreateSegment={setShowCreateSegment}
                onCompareChange={setIsComparing}
                readOnly={
                  !manageSegmentOverrides ||
                  !!freeze?.isFrozen ||
                  !!freeze?.isLoading
                }
                is4Eyes={is4Eyes}
                showEditSegment
                showCreateSegment={showCreateSegment}
                feature={projectFlag.id}
                projectId={projectId}
                multivariateOptions={projectFlag.multivariate_options}
                environmentId={environmentId}
                value={segmentOverrides}
                controlValue={controlValue}
                controlEnabled={controlEnabled}
                onChange={(v: SegmentOverrideValue[]) => {
                  onSegmentsChange()
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
          {!isComparing && !showCreateSegment && !freeze?.isFrozen && (
            <ModalHR className='mt-4' />
          )}
          {!isComparing && !showCreateSegment && !freeze?.isFrozen && (
            <div>
              <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                Re-order overrides to adjust priority.
              </p>
              <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                {is4Eyes && isVersioned
                  ? 'This will create a change request with any value and segment override changes for the environment'
                  : 'This will update the segment overrides for the environment'}{' '}
                <strong>{environmentName}</strong>
              </p>
              {is4Eyes && !isVersioned && (
                <InfoMessage>
                  Enable Feature Versioning to gate segment overrides with
                  Feature Change Requests.{' '}
                  <a
                    href='https://docs.flagsmith.com/managing-flags/feature-versioning'
                    target='_blank'
                    rel='noreferrer'
                  >
                    Learn more
                  </a>
                  .
                </InfoMessage>
              )}
              <div className='text-right'>
                {isVersioned && is4Eyes
                  ? Utils.renderWithPermission(
                      savePermission,
                      Utils.getManageFeaturePermissionDescription(is4Eyes),
                      <Button
                        onClick={() => saveFeatureSegments(false)}
                        type='button'
                        data-test='update-feature-segments-btn'
                        id='update-feature-segments-btn'
                        disabled={
                          isSaving ||
                          !projectFlag.name ||
                          invalid ||
                          !savePermission ||
                          !!freeze?.isLoading
                        }
                      >
                        {getButtonText()}
                      </Button>,
                    )
                  : Utils.renderWithPermission(
                      manageSegmentOverrides,
                      Constants.environmentPermissions(
                        EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
                      ),
                      <>
                        {!is4Eyes && isVersioned && (
                          <>
                            <Button
                              theme='secondary'
                              onClick={() => saveFeatureSegments(true)}
                              className='mr-2'
                              type='button'
                              data-test='create-change-request'
                              id='create-change-request-btn'
                              disabled={
                                isSaving ||
                                !projectFlag.name ||
                                invalid ||
                                !savePermission ||
                                !!freeze?.isLoading
                              }
                            >
                              {getScheduleButtonText()}
                            </Button>
                          </>
                        )}
                        <Button
                          onClick={() => saveFeatureSegments(false)}
                          type='button'
                          data-test='update-feature-segments-btn'
                          id='update-feature-segments-btn'
                          disabled={
                            isSaving ||
                            !projectFlag.name ||
                            invalid ||
                            !manageSegmentOverrides ||
                            !!freeze?.isLoading
                          }
                        >
                          {isSaving ? 'Updating' : 'Update Segment Overrides'}
                        </Button>
                      </>,
                    )}
              </div>
            </div>
          )}
        </div>
      </FeatureInPipelineGuard>
    </FormGroup>
  )
}

export default SegmentOverridesTab
