import _ from 'lodash'
import { useMemo } from 'react'

import Utils from 'common/utils/utils'
import ModalHR from './ModalHR'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import { Identity } from 'common/types/responses'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import AddToReleasePipelineModal from 'components/release-pipelines/AddToReleasePipelineModal'
import RemoveFromReleasePipelineModal from 'components/release-pipelines/RemoveFromReleasePipelineModal'
import ButtonDropdown from 'components/base/forms/ButtonDropdown'
import Button from 'components/base/forms/Button'

export interface FlagValueFooterProps {
  is4Eyes: boolean
  isVersioned: boolean
  projectId: number
  projectFlag: any
  environmentId: string
  environmentName: string
  isSaving: boolean
  featureName: string
  isInvalid: boolean
  existingChangeRequest: boolean
  onSaveFeatureValue: (schedule?: boolean) => void
  identity: Identity
}

const FlagValueFooter = ({
  environmentId,
  environmentName,
  existingChangeRequest,
  featureName,
  identity,
  is4Eyes,
  isInvalid,
  isSaving,
  isVersioned,
  onSaveFeatureValue,
  projectFlag,
  projectId,
}: FlagValueFooterProps) => {
  const isReleasePipelineEnabled =
    Utils.getFlagsmithHasFeature('release_pipelines')
  const featureId = projectFlag.id

  const { data: releasePipelines } = useGetReleasePipelinesQuery(
    {
      projectId: Number(projectId),
    },
    {
      skip: !projectId,
    },
  )

  const releasePipeline = useMemo(
    () =>
      releasePipelines?.results?.find((pipeline) =>
        pipeline.features?.includes(featureId),
      ),
    [releasePipelines, featureId],
  )
  const hasPublishedReleasePipelines = useMemo(
    () => releasePipelines?.results?.some((pipeline) => pipeline.published_at),
    [releasePipelines],
  )

  const openReleasePipelineModal = () => {
    openModal2(
      `Add ${featureName} To Release Pipeline`,
      <AddToReleasePipelineModal projectId={projectId} featureId={featureId} />,
    )
  }

  const removeFromReleasePipeline = () => {
    if (!releasePipeline) {
      return
    }

    openModal2(
      `Remove ${featureName} From ${releasePipeline.name} Pipeline`,
      <RemoveFromReleasePipelineModal
        projectId={projectId}
        featureId={featureId}
        pipelineId={releasePipeline.id}
      />,
    )
  }

  const releasePipelineOption = {
    label: releasePipeline?.id
      ? 'Remove from Release Pipeline'
      : 'Add to Release Pipeline',
    onClick: releasePipeline?.id
      ? removeFromReleasePipeline
      : openReleasePipelineModal,
  }

  return (
    <Permission level='project' permission='ADMIN' id={projectId}>
      {({ permission: projectAdmin }) => (
        <>
          <ModalHR className='mt-4' />
          <div className='text-right mt-4 mb-3 fs-small lh-sm modal-caption'>
            {is4Eyes
              ? `This will create a change request ${
                  isVersioned
                    ? 'with any value and segment override changes '
                    : ''
                }for the environment`
              : 'This will update the feature value for the environment'}{' '}
            <strong>{environmentName}</strong>
          </div>
          <div className='text-right'>
            <Permission
              level='environment'
              tags={projectFlag?.tags}
              permission={Utils.getManageFeaturePermission(is4Eyes, identity)}
              id={environmentId}
            >
              {({ permission: savePermission }) =>
                Utils.renderWithPermission(
                  savePermission,
                  Constants.environmentPermissions(
                    Utils.getManageFeaturePermissionDescription(
                      is4Eyes,
                      identity,
                    ),
                  ),
                  <>
                    {!is4Eyes && (
                      <Button
                        feature='SCHEDULE_FLAGS'
                        theme='secondary'
                        onClick={() => onSaveFeatureValue(true)}
                        className='mr-2'
                        type='button'
                        data-test='create-change-request'
                        id='create-change-request-btn'
                        disabled={
                          isSaving ||
                          !featureName ||
                          isInvalid ||
                          !savePermission
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
                    )}
                    <ButtonDropdown
                      onClick={() => onSaveFeatureValue()}
                      type='button'
                      data-test='update-feature-btn'
                      id='update-feature-btn'
                      toggleIcon='plus'
                      disabled={
                        !savePermission || isSaving || !featureName || isInvalid
                      }
                      dropdownItems={[
                        ...(isReleasePipelineEnabled &&
                        hasPublishedReleasePipelines &&
                        projectAdmin
                          ? [releasePipelineOption]
                          : []),
                      ]}
                    >
                      {isSaving
                        ? is4Eyes
                          ? existingChangeRequest
                            ? 'Updating Change Request'
                            : 'Creating Change Request'
                          : 'Updating'
                        : is4Eyes
                        ? existingChangeRequest
                          ? 'Update Change Request'
                          : 'Create Change Request'
                        : 'Update Feature Value'}
                    </ButtonDropdown>
                  </>,
                )
              }
            </Permission>
          </div>
        </>
      )}
    </Permission>
  )
}

export { FlagValueFooter }
