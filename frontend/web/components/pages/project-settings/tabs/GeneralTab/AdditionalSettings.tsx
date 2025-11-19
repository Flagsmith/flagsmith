import React from 'react'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'
import Setting from 'components/Setting'
import { Project } from 'common/types/responses'
import Utils from 'common/utils/utils'

type AdditionalSettingsProps = {
  project: Project
  minimumChangeRequestApprovals: number | null
  onChangeRequestsToggle: (value: number | null) => void
  onChangeRequestsChange: (value: number | null) => void
  onPreventDefaultsToggle: () => void
  onCaseSensitivityToggle: () => void
  onSave: () => void
  isSaving: boolean
}

export const AdditionalSettings = ({
  isSaving,
  minimumChangeRequestApprovals,
  onCaseSensitivityToggle,
  onChangeRequestsChange,
  onChangeRequestsToggle,
  onPreventDefaultsToggle,
  onSave,
  project,
}: AdditionalSettingsProps) => {
  const changeRequestsFeature = Utils.getFlagsmithHasFeature(
    'segment_change_requests',
  )

  const settings = [
    {
      checked: project.prevent_flag_defaults,
      'data-test': 'js-prevent-flag-defaults',
      description: `By default, when you create a feature with a value and
                          enabled state it acts as a default for your other
                          environments. Enabling this setting forces the user to
                          create a feature before setting its values per
                          environment.`,
      onChange: onPreventDefaultsToggle,
      title: 'Prevent Flag Defaults',
    },
    {
      checked: !project.only_allow_lower_case_feature_names,
      'data-test': 'js-flag-case-sensitivity',
      description: `By default, features are lower case in order to
                          prevent human error. Enabling this will allow you to
                          use upper case characters when creating features.`,
      onChange: onCaseSensitivityToggle,
      title: 'Case sensitive features',
    },
  ]

  return (
    <div>
      {changeRequestsFeature && (
        <ChangeRequestsSetting
          feature='4_EYES_PROJECT'
          value={minimumChangeRequestApprovals}
          onToggle={onChangeRequestsToggle}
          onSave={onSave}
          onChange={onChangeRequestsChange}
          isLoading={isSaving}
        />
      )}
      {settings.map((setting) => (
        <Setting
          key={setting['data-test']}
          title={setting.title}
          data-test={setting['data-test']}
          disabled={isSaving}
          onChange={setting.onChange}
          checked={setting.checked}
          description={setting.description}
        />
      ))}
    </div>
  )
}
