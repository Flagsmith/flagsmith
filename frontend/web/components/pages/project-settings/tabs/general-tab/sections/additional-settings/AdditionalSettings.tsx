import React from 'react'
import { Project } from 'common/types/responses'
import { ChangeRequestsApprovalsSetting } from './ChangeRequestsApprovalsSetting'
import { PreventFlagDefaultsSetting } from './PreventFlagDefaultsSetting'
import { CaseSensitivitySetting } from './CaseSensitivitySetting'
import { FeatureNameValidation } from './FeatureNameValidation'

type AdditionalSettingsProps = {
  project: Project
}

export const AdditionalSettings = ({ project }: AdditionalSettingsProps) => {
  return (
    <div>
      <ChangeRequestsApprovalsSetting project={project} />

      <PreventFlagDefaultsSetting project={project} />

      <CaseSensitivitySetting project={project} />

      <FeatureNameValidation project={project} />
    </div>
  )
}
