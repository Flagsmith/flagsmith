import React, { useMemo } from 'react'
import Button from './base/forms/Button'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { Identity, ProjectFlag } from 'common/types/responses'
import Utils from 'common/utils/utils'

interface SegmentTabFooterProps {
  is4Eyes: boolean
  isVersioned: boolean
  isSaving: boolean
  name: string
  invalid: boolean
  existingChangeRequest: any
  saveFeatureSegments: (schedule?: boolean) => void
  projectFlag: ProjectFlag
  environmentId: string
  identity?: Identity
  projectId: number
}

const FEATURE_IN_RELEASE_PIPELINE_TEXT =
  'This feature is in a release pipeline and cannot have segment override changes.'

const SegmentTabFooter: React.FC<SegmentTabFooterProps> = ({
  environmentId,
  existingChangeRequest,
  identity,
  invalid,
  is4Eyes,
  isSaving,
  isVersioned,
  name,
  projectFlag,
  projectId,
  saveFeatureSegments,
}) => {
  const featureId = projectFlag?.id
  const { data: releasePipelines } = useGetReleasePipelinesQuery(
    {
      projectId: projectId,
    },
    {
      skip: !projectFlag?.id,
    },
  )

  const isFeatureInReleasePipeline = useMemo(() => {
    if (!featureId) {
      return false
    }

    return releasePipelines?.results?.some((pipeline) =>
      pipeline.features?.includes(featureId),
    )
  }, [releasePipelines, featureId])

  return (
    <Permission
      level='environment'
      tags={projectFlag.tags}
      permission={Utils.getManageFeaturePermission(is4Eyes, identity)}
      id={environmentId}
    >
      {({ permission: savePermission }) => (
        <Permission
          level='environment'
          permission='MANAGE_SEGMENT_OVERRIDES'
          id={environmentId}
        >
          {({ permission: manageSegmentsOverrides }) => {
            if (isVersioned && is4Eyes) {
              return Utils.renderWithPermission(
                savePermission,
                Utils.getManageFeaturePermissionDescription(is4Eyes, identity),
                <Button
                  onClick={() => saveFeatureSegments(false)}
                  type='button'
                  data-test='update-feature-segments-btn'
                  id='update-feature-segments-btn'
                  disabled={isSaving || !name || invalid || !savePermission}
                >
                  {isSaving
                    ? existingChangeRequest
                      ? 'Updating Change Request'
                      : 'Creating Change Request'
                    : existingChangeRequest
                    ? 'Update Change Request'
                    : 'Create Change Request'}
                </Button>,
              )
            }

            return Utils.renderWithPermission(
              manageSegmentsOverrides,
              Constants.environmentPermissions('Manage segment overrides'),
              <>
                {!is4Eyes && isVersioned && (
                  <Tooltip
                    title={
                      <Button
                        feature='SCHEDULE_FLAGS'
                        theme='secondary'
                        onClick={() => saveFeatureSegments(true)}
                        className='mr-2'
                        type='button'
                        data-test='create-change-request'
                        id='create-change-request-btn'
                        disabled={
                          isSaving ||
                          !name ||
                          invalid ||
                          !savePermission ||
                          isFeatureInReleasePipeline
                        }
                      >
                        {isSaving
                          ? existingChangeRequest
                            ? 'Updating Change Request'
                            : 'Scheduling Update'
                          : existingChangeRequest
                          ? 'Update Change Request'
                          : 'Schedule Update'}
                      </Button>
                    }
                  >
                    {isFeatureInReleasePipeline
                      ? FEATURE_IN_RELEASE_PIPELINE_TEXT
                      : ''}
                  </Tooltip>
                )}
                <Tooltip
                  title={
                    <Button
                      onClick={() => saveFeatureSegments(false)}
                      type='button'
                      data-test='update-feature-segments-btn'
                      id='update-feature-segments-btn'
                      disabled={
                        isSaving ||
                        !name ||
                        invalid ||
                        !manageSegmentsOverrides ||
                        isFeatureInReleasePipeline
                      }
                    >
                      {isSaving ? 'Updating' : 'Update Segment Overrides'}
                    </Button>
                  }
                >
                  {isFeatureInReleasePipeline
                    ? FEATURE_IN_RELEASE_PIPELINE_TEXT
                    : ''}
                </Tooltip>
              </>,
            )
          }}
        </Permission>
      )}
    </Permission>
  )
}

export default SegmentTabFooter
