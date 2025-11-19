import React, { useCallback } from 'react'
import Setting from 'components/Setting'
import ConfirmHideFlags from 'components/modals/ConfirmHideFlags'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type SDKSettingsTabProps = {
  project: Project
}

export const SDKSettingsTab = ({ project }: SDKSettingsTabProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()

  const handleRealtimeToggle = useCallback(async () => {
    await updateProjectWithToast(
      {
        enable_realtime_updates: !project.enable_realtime_updates,
        name: project.name,
      },
      project.id,
      {
        errorMessage: 'Failed to update realtime settings. Please try again.',
      },
    )
  }, [
    project.name,
    project.enable_realtime_updates,
    project.id,
    updateProjectWithToast,
  ])

  const handleHideDisabledFlagsToggle = useCallback(async () => {
    await updateProjectWithToast(
      {
        hide_disabled_flags: !project.hide_disabled_flags,
        name: project.name,
      },
      project.id,
      {
        errorMessage: 'Failed to update hide disabled flags. Please try again.',
      },
    )
  }, [
    project.name,
    project.hide_disabled_flags,
    project.id,
    updateProjectWithToast,
  ])

  const toggleHideDisabledFlags = () => {
    openModal(
      'Hide Disabled Flags',
      <ConfirmHideFlags
        project={project}
        value={!!project.hide_disabled_flags}
        cb={handleHideDisabledFlagsToggle}
      />,
      'p-0 modal-sm',
    )
  }

  return (
    <div className='col-md-8 m-4'>
      <div className='d-flex flex-column gap-4'>
        <div>
          <Setting
            feature='REALTIME'
            disabled={isSaving}
            onChange={handleRealtimeToggle}
            checked={project.enable_realtime_updates}
          />
        </div>
        <div>
          <Setting
            data-test='js-hide-disabled-flags'
            disabled={isSaving}
            onChange={toggleHideDisabledFlags}
            checked={project.hide_disabled_flags}
            title='Hide disabled flags from SDKs'
            description='To prevent letting your users know about your upcoming features and to cut down on payload, enabling this will prevent the API from returning features that are disabled.'
          />
        </div>
      </div>
    </div>
  )
}
