import React from 'react'
import Setting from 'components/Setting'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type CaseSensitivitySettingProps = {
  project: Project
}

export const CaseSensitivitySetting = ({
  project,
}: CaseSensitivitySettingProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()

  const handleToggle = async () => {
    await updateProjectWithToast(
      {
        name: project.name,
        only_allow_lower_case_feature_names:
          !project.only_allow_lower_case_feature_names,
      },
      project.id,
    )
  }

  return (
    <Setting
      data-test='js-flag-case-sensitivity'
      disabled={isSaving}
      onChange={handleToggle}
      checked={project.only_allow_lower_case_feature_names}
      title='Force Flag names to lowercase'
      description='When enabled, all feature names will be converted to lower case'
    />
  )
}
