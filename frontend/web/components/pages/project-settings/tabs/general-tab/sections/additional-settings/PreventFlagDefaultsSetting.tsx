import React, { useCallback } from 'react'
import Setting from 'components/Setting'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type PreventFlagDefaultsSettingProps = {
  project: Project
}

export const PreventFlagDefaultsSetting = ({
  project,
}: PreventFlagDefaultsSettingProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()

  const handleToggle = useCallback(async () => {
    await updateProjectWithToast(
      {
        name: project.name,
        prevent_flag_defaults: !project.prevent_flag_defaults,
      },
      project.id,
    )
  }, [
    project.name,
    project.prevent_flag_defaults,
    project.id,
    updateProjectWithToast,
  ])

  return (
    <Setting
      title='Prevent Flag Defaults'
      data-test='js-prevent-flag-defaults'
      description={`By default, when you create a feature with a value and
                          enabled state it acts as a default for your other
                          environments. Enabling this setting forces the user to
                          create a feature before setting its values per
                          environment.`}
      disabled={isSaving}
      onChange={handleToggle}
      checked={project.prevent_flag_defaults}
    />
  )
}
