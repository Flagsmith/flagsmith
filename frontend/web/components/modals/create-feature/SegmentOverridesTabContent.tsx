import React, { FC } from 'react'
import FormGroup from 'components/base/forms/FormGroup'
import SegmentOverrides from 'components/SegmentOverrides'
import Button from 'components/base/forms/Button'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import ModalHR from 'components/modals/ModalHR'
import Icon from 'components/Icon'
import FeatureInPipelineGuard from 'components/release-pipelines/FeatureInPipelineGuard'
import { FeatureState, ProjectFlag } from 'common/types/responses'

type SegmentOverridesTabContentProps = {
  projectId: number
  projectFlag: ProjectFlag
  environmentId: string
  environmentName: string
  segmentOverrides?: FeatureState[]
  showCreateSegment: boolean
  manageSegmentOverrides: boolean
  savePermission: boolean
  is4Eyes: boolean
  isVersioned: boolean
  isSaving: boolean
  invalid: boolean
  noPermissions?: boolean
  enabledSegment: boolean
  featureError: string
  featureWarning: string
  controlValue: any
  highlightSegmentId?: number
  existingChangeRequest?: any
  disableCreate?: boolean
  onSetShowCreateSegment: (show: boolean) => void
  onChangeSegment: (items: FeatureState[]) => void
  onUpdateSegments: (segments: FeatureState[]) => void
  onSaveFeatureSegments: (schedule: boolean) => void
}

const SegmentOverridesTabContent: FC<SegmentOverridesTabContentProps> = ({
  controlValue,
  disableCreate,
  enabledSegment,
  environmentId,
  environmentName,
  existingChangeRequest,
  featureError,
  featureWarning,
  highlightSegmentId,
  invalid,
  is4Eyes,
  isSaving,
  isVersioned,
  manageSegmentOverrides,
  noPermissions,
  onChangeSegment,
  onSaveFeatureSegments,
  onSetShowCreateSegment,
  onUpdateSegments,
  projectFlag,
  projectId,
  savePermission,
  segmentOverrides,
  showCreateSegment,
}) => {
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

  return (
    <FormGroup className='mb-4'>
      <FeatureInPipelineGuard
        projectId={projectId}
        featureId={projectFlag?.id}
        renderFallback={(matchingReleasePipeline: { name: string }) => (
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
            {!showCreateSegment &&
              !!manageSegmentOverrides &&
              !disableCreate && (
                <div className='text-right'>
                  <Button
                    size='small'
                    onClick={() => {
                      onSetShowCreateSegment(true)
                    }}
                    theme='outline'
                    disabled={false}
                  >
                    Create Feature-Specific Segment
                  </Button>
                </div>
              )}
            {!showCreateSegment && !noPermissions && (
              <Button
                onClick={() => onChangeSegment(segmentOverrides || [])}
                type='button'
                theme='secondary'
                size='small'
              >
                {enabledSegment ? 'Enable All' : 'Disable All'}
              </Button>
            )}
          </Row>
          {segmentOverrides ? (
            <>
              <ErrorMessage error={featureError} />
              <WarningMessage warningMessage={featureWarning} />
              <SegmentOverrides
                setShowCreateSegment={onSetShowCreateSegment}
                readOnly={!manageSegmentOverrides}
                is4Eyes={is4Eyes}
                showEditSegment
                showCreateSegment={showCreateSegment}
                feature={projectFlag.id}
                projectId={projectId}
                multivariateOptions={projectFlag.multivariate_options}
                environmentId={environmentId}
                value={segmentOverrides}
                controlValue={controlValue}
                onChange={(v: FeatureState[]) => {
                  onUpdateSegments(v)
                }}
                highlightSegmentId={highlightSegmentId}
              />
            </>
          ) : (
            <div className='text-center'>
              <Loader />
            </div>
          )}
          {!showCreateSegment && <ModalHR className='mt-4' />}
          {!showCreateSegment && (
            <div>
              <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                {is4Eyes && isVersioned
                  ? 'This will create a change request with any value and segment override changes for the environment'
                  : 'This will update the segment overrides for the environment'}{' '}
                <strong>{environmentName}</strong>
              </p>
              <div className='text-right'>
                {(() => {
                  if (isVersioned && is4Eyes) {
                    return Utils.renderWithPermission(
                      savePermission,
                      Utils.getManageFeaturePermissionDescription(
                        is4Eyes,
                        null,
                      ),
                      <Button
                        onClick={() => onSaveFeatureSegments(false)}
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
                            onClick={() => onSaveFeatureSegments(true)}
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
                        onClick={() => onSaveFeatureSegments(false)}
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
                        {isSaving ? 'Updating' : 'Update Segment Overrides'}
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
  )
}

export default SegmentOverridesTabContent
