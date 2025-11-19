import React, { useCallback, useEffect, useState } from 'react'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'
import { PreventFlagDefaultsSetting } from './PreventFlagDefaultsSetting'
import { CaseSensitivitySetting } from './CaseSensitivitySetting'
import { FeatureNameValidation } from './FeatureNameValidation'

type AdditionalSettingsProps = {
  project: Project
}

export const AdditionalSettings = ({ project }: AdditionalSettingsProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()
  const [minimumChangeRequestApprovals, setMinimumChangeRequestApprovals] =
    useState(project.minimum_change_request_approvals)

  const changeRequestsFeature = Utils.getFlagsmithHasFeature(
    'segment_change_requests',
  )

  // Sync local state when project changes
  useEffect(() => {
    if (project) {
      setMinimumChangeRequestApprovals(project.minimum_change_request_approvals)
    }
  }, [project])

  const saveChangeRequests = useCallback(async () => {
    if (isSaving) return

    await updateProjectWithToast(
      {
        minimum_change_request_approvals: minimumChangeRequestApprovals,
        name: project.name,
      },
      project.id,
      {
        errorMessage: 'Failed to save project. Please try again.',
        successMessage: 'Project Saved',
      },
    )
  }, [
    minimumChangeRequestApprovals,
    project.name,
    project.id,
    isSaving,
    updateProjectWithToast,
  ])

  const handleChangeRequestsToggle = useCallback(
    (value: number | null) => {
      setMinimumChangeRequestApprovals(value)
      // Auto-save on toggle
      saveChangeRequests()
    },
    [saveChangeRequests],
  )

  return (
    <div>
      {changeRequestsFeature && (
        <ChangeRequestsSetting
          feature='4_EYES_PROJECT'
          value={minimumChangeRequestApprovals}
          onToggle={handleChangeRequestsToggle}
          onSave={saveChangeRequests}
          onChange={setMinimumChangeRequestApprovals}
          isLoading={isSaving}
        />
      )}

      <PreventFlagDefaultsSetting project={project} />

      <CaseSensitivitySetting project={project} />

      <FeatureNameValidation project={project} />
    </div>
  )
}
