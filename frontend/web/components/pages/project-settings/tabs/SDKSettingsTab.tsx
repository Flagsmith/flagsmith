import React, { useCallback } from 'react'
import Setting from 'components/Setting'
import ConfirmHideFlags from 'components/modals/ConfirmHideFlags'
import { Project } from 'common/types/responses'
import { useUpdateProjectMutation } from 'common/services/useProject'

type SDKSettingsTabProps = {
  project: Project
  projectId: number
  environmentId?: string
}

export const SDKSettingsTab = ({ project, projectId }: SDKSettingsTabProps) => {
  const [updateProject, { isLoading: isSaving }] = useUpdateProjectMutation()

  const handleRealtimeToggle = useCallback(async () => {
    await updateProject({
      body: {
        enable_realtime_updates: !project.enable_realtime_updates,
      },
      id: String(projectId),
    })
  }, [project.enable_realtime_updates, projectId, updateProject])

  const handleHideDisabledFlagsToggle = useCallback(async () => {
    await updateProject({
      body: {
        hide_disabled_flags: !project.hide_disabled_flags,
      },
      id: String(projectId),
    })
  }, [project.hide_disabled_flags, projectId, updateProject])

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
