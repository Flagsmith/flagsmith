import React from 'react'
import Setting from 'components/Setting'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Utils from 'common/utils/utils'

type EnforceFeatureOwnershipSettingProps = {
  project: Project
}

export const EnforceFeatureOwnershipSetting = ({
  project,
}: EnforceFeatureOwnershipSettingProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()
  const hasFlagOwnersPlan = Utils.getPlansPermission('FLAG_OWNERS')

  const handleToggle = async () => {
    await updateProjectWithToast(
      {
        enforce_feature_owners: !project.enforce_feature_owners,
        name: project.name,
      },
      project.id,
    )
  }

  if (!hasFlagOwnersPlan) {
    return (
      <PlanBasedBanner
        className='mb-3'
        feature={'FLAG_OWNERS'}
        theme={'description'}
        title='Enforce Feature Ownership'
      />
    )
  }

  return (
    <Setting
      title='Enforce Feature Ownership'
      data-test='js-enforce-feature-owners'
      description={`When enabled, at least one user or group owner must be
                        assigned when creating a feature. This ensures every
                        feature has a clear point of accountability.`}
      disabled={isSaving}
      onChange={handleToggle}
      checked={project.enforce_feature_owners}
    />
  )
}
