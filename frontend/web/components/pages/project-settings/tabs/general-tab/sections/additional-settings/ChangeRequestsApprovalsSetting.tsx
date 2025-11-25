import React, { useState } from 'react'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type ChangeRequestsApprovalsSettingProps = {
  project: Project
}

export const ChangeRequestsApprovalsSetting = ({
  project,
}: ChangeRequestsApprovalsSettingProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()
  const [minimumChangeRequestApprovals, setMinimumChangeRequestApprovals] =
    useState(project.minimum_change_request_approvals ?? null)

  const changeRequestsFeature = Utils.getFlagsmithHasFeature(
    'segment_change_requests',
  )

  const saveChangeRequests = async (value: number | null) => {
    if (isSaving) return

    await updateProjectWithToast(
      {
        minimum_change_request_approvals: value,
        name: project.name,
      },
      project.id,
      {
        errorMessage: 'Failed to save project. Please try again.',
        successMessage: 'Project Saved',
      },
    )
  }

  const handleChangeRequestsToggle = (value: number | null) => {
    setMinimumChangeRequestApprovals(value)
    saveChangeRequests(value)
  }

  if (!changeRequestsFeature) {
    return null
  }

  return (
    <ChangeRequestsSetting
      data-test='js-change-request-approvals'
      feature='4_EYES_PROJECT'
      value={minimumChangeRequestApprovals}
      onToggle={handleChangeRequestsToggle}
      onSave={() => saveChangeRequests(minimumChangeRequestApprovals)}
      onChange={setMinimumChangeRequestApprovals}
      isLoading={isSaving}
    />
  )
}
