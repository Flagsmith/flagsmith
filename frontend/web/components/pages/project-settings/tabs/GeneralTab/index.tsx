import React, { useCallback, useEffect, useState } from 'react'
import { useHistory } from 'react-router-dom'
import JSONReference from 'components/JSONReference'
import SettingTitle from 'components/SettingTitle'
import { Project } from 'common/types/responses'
import { useUpdateProjectMutation } from 'common/services/useProject'
import Utils from 'common/utils/utils'
import { ProjectInformation } from './ProjectInformation'
import { AdditionalSettings } from './AdditionalSettings'
import { FeatureNameValidation } from './FeatureNameValidation'
import { EdgeAPIMigration } from './EdgeAPIMigration'
import { DeleteProject } from './DeleteProject'

type GeneralTabProps = {
  project: Project
  projectId: number
  environmentId?: string
}

export const GeneralTab = ({ project, projectId }: GeneralTabProps) => {
  const history = useHistory()
  const [updateProject, { isLoading: isSaving }] = useUpdateProjectMutation()

  const [name, setName] = useState(project.name)
  const [staleFlagsLimitDays, setStaleFlagsLimitDays] = useState(
    project.stale_flags_limit_days,
  )
  const [minimumChangeRequestApprovals, setMinimumChangeRequestApprovals] =
    useState(project.minimum_change_request_approvals)
  const [featureNameRegex, setFeatureNameRegex] = useState<string | null>(
    project.feature_name_regex || null,
  )

  // Sync local state when project changes
  useEffect(() => {
    if (project) {
      setName(project.name)
      setStaleFlagsLimitDays(project.stale_flags_limit_days)
      setMinimumChangeRequestApprovals(project.minimum_change_request_approvals)
      setFeatureNameRegex(project.feature_name_regex || null)
    }
  }, [project])

  const saveProject = useCallback(async () => {
    if (!name || isSaving) return

    await updateProject({
      body: {
        minimum_change_request_approvals: minimumChangeRequestApprovals,
        name,
        stale_flags_limit_days: staleFlagsLimitDays,
      },
      id: String(projectId),
    })
    toast('Project Saved')
  }, [
    name,
    staleFlagsLimitDays,
    minimumChangeRequestApprovals,
    projectId,
    isSaving,
    updateProject,
  ])

  const handlePreventDefaultsToggle = useCallback(async () => {
    await updateProject({
      body: {
        prevent_flag_defaults: !project.prevent_flag_defaults,
      },
      id: String(projectId),
    })
  }, [project.prevent_flag_defaults, projectId, updateProject])

  const handleCaseSensitivityToggle = useCallback(async () => {
    await updateProject({
      body: {
        only_allow_lower_case_feature_names:
          !project.only_allow_lower_case_feature_names,
      },
      id: String(projectId),
    })
  }, [project.only_allow_lower_case_feature_names, projectId, updateProject])

  const handleFeatureValidationToggle = useCallback(() => {
    if (featureNameRegex) {
      setFeatureNameRegex(null)
      updateProject({
        body: {
          feature_name_regex: null,
        },
        id: String(projectId),
      })
    } else {
      setFeatureNameRegex('^.+$')
    }
  }, [featureNameRegex, projectId, updateProject])

  const handleFeatureNameRegexSave = useCallback(async () => {
    await updateProject({
      body: {
        feature_name_regex: featureNameRegex,
      },
      id: String(projectId),
    })
  }, [featureNameRegex, projectId, updateProject])

  const handleChangeRequestsToggle = useCallback(
    (value: number | null) => {
      setMinimumChangeRequestApprovals(value)
      saveProject()
    },
    [saveProject],
  )

  const handleDelete = useCallback(() => {
    history.replace(Utils.getOrganisationHomePage())
  }, [history])

  return (
    <div className='mt-4 col-md-8'>
      <JSONReference title='Project' json={project} className='mb-3' />

      <SettingTitle>Project Information</SettingTitle>
      <label>Project Name</label>

      <ProjectInformation
        name={name}
        staleFlagsLimitDays={staleFlagsLimitDays}
        onNameChange={setName}
        onStaleFlagsChange={setStaleFlagsLimitDays}
        onSubmit={saveProject}
        isSaving={isSaving}
      />

      <SettingTitle>Additional Settings</SettingTitle>

      <AdditionalSettings
        project={project}
        minimumChangeRequestApprovals={minimumChangeRequestApprovals}
        onChangeRequestsToggle={handleChangeRequestsToggle}
        onChangeRequestsChange={setMinimumChangeRequestApprovals}
        onPreventDefaultsToggle={handlePreventDefaultsToggle}
        onCaseSensitivityToggle={handleCaseSensitivityToggle}
        onSave={saveProject}
        isSaving={isSaving}
      />

      <FeatureNameValidation
        featureNameRegex={featureNameRegex}
        onToggle={handleFeatureValidationToggle}
        onChange={setFeatureNameRegex}
        onSave={handleFeatureNameRegexSave}
        isSaving={isSaving}
      />

      <EdgeAPIMigration project={project} />

      <DeleteProject project={project} onDelete={handleDelete} />
    </div>
  )
}
