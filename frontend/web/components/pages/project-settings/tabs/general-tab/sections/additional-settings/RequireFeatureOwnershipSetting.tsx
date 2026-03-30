import React from 'react'
import SettingRow from 'components/SettingRow'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type RequireFeatureOwnershipSettingProps = {
  project: Project
}

export const RequireFeatureOwnershipSetting = ({
  project,
}: RequireFeatureOwnershipSettingProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()

  const handleToggle = async () => {
    await updateProjectWithToast(
      {
        name: project.name,
        require_feature_owners: !project.require_feature_owners,
      },
      project.id,
    )
  }

  return (
    <SettingRow
      title='Require feature ownership'
      description='When enabled, users must assign at least one owner (user or group) when creating a feature flag. This improves governance by ensuring every feature has a responsible party.'
      checked={!!project.require_feature_owners}
      disabled={isSaving}
      onChange={handleToggle}
      data-test='js-require-feature-ownership'
    />
  )
}
