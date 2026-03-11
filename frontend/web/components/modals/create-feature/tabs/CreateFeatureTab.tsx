import React, { FC, useCallback, useEffect, useState } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValueTab from './FeatureValueTab'
import FeatureSettingsTab from './FeatureSettingsTab'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'
import {
  ADMIN_PERMISSION,
  ProjectPermission,
} from 'common/types/permissions.types'
import Switch from 'components/Switch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import { useCreateTagMutation, useGetTagsQuery } from 'common/services/useTag'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  featureState: FeatureState
  overrideFeatureState?: FeatureState
  projectFlag: ProjectFlag | null
  identity?: string
  defaultExperiment?: boolean
  onEnvironmentFlagChange: (changes: Partial<FeatureState>) => void
  onProjectFlagChange: (changes: Partial<ProjectFlag>) => void
  onRemoveMultivariateOption?: (id: number) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeatureTab: FC<CreateFeatureTabProps> = ({
  defaultExperiment,
  error,
  featureError,
  featureState,
  featureWarning,
  identity,
  onEnvironmentFlagChange,
  onHasMetadataRequiredChange,
  onProjectFlagChange,
  onRemoveMultivariateOption,
  overrideFeatureState,
  projectFlag,
  projectId,
}) => {
  const { permission: createFeature } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.CREATE_FEATURE,
  })

  const { permission: projectAdmin } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ADMIN_PERMISSION,
  })

  const noPermissions = !createFeature && !projectAdmin

  const showExperimentToggle =
    Utils.getFlagsmithHasFeature('experimental_flags') && !identity

  const { data: tags } = useGetTagsQuery(
    { projectId },
    { skip: !showExperimentToggle },
  )
  const [createTag] = useCreateTagMutation()

  const [isExperimentFlag, setIsExperimentFlag] = useState(!!defaultExperiment)

  const hasVariants = (projectFlag?.multivariate_options?.length ?? 0) > 0

  // Auto-untoggle if all variants are removed
  useEffect(() => {
    if (!hasVariants && isExperimentFlag) {
      setIsExperimentFlag(false)
      if (projectFlag && tags) {
        const experimentTag = tags.find(
          (t) => t.label.toLowerCase() === 'experiment',
        )
        if (experimentTag) {
          onProjectFlagChange({
            ...projectFlag,
            tags: projectFlag.tags.filter((id) => id !== experimentTag.id),
          })
        }
      }
    }
  }, [hasVariants]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleExperimentToggle = useCallback(
    async (checked: boolean) => {
      if (!projectFlag || !tags) return

      setIsExperimentFlag(checked)

      let experimentTag = tags.find(
        (t) => t.label.toLowerCase() === 'experiment',
      )

      if (checked) {
        if (!experimentTag) {
          experimentTag = await createTag({
            projectId,
            tag: {
              color: '#6A52CF',
              description: 'Experiment flag',
              label: 'experiment',
            },
          }).unwrap()
        }
        if (experimentTag && !projectFlag.tags.includes(experimentTag.id)) {
          onProjectFlagChange({
            ...projectFlag,
            tags: [...projectFlag.tags, experimentTag.id],
          })
        }
      } else {
        if (experimentTag) {
          onProjectFlagChange({
            ...projectFlag,
            tags: projectFlag.tags.filter((id) => id !== experimentTag?.id),
          })
        }
      }
    },
    [projectFlag, tags, createTag, projectId, onProjectFlagChange],
  )

  return (
    <>
      <ErrorMessage error={featureError} />
      <WarningMessage warningMessage={featureWarning} />
      {!!projectFlag && (
        <>
          <FeatureValueTab
            error={error}
            projectId={projectId}
            identity={identity}
            noPermissions={noPermissions}
            featureState={overrideFeatureState || featureState}
            projectFlag={projectFlag}
            onEnvironmentFlagChange={onEnvironmentFlagChange}
            onProjectFlagChange={onProjectFlagChange}
            onRemoveMultivariateOption={onRemoveMultivariateOption}
          />
          {showExperimentToggle && (
            <FormGroup className='my-4'>
              <Tooltip
                title={
                  <div className='flex-row'>
                    <Switch
                      checked={isExperimentFlag}
                      onChange={handleExperimentToggle}
                      disabled={!hasVariants}
                      className='ml-0'
                    />
                    <div className='label-switch ml-3 mr-1'>
                      Experiment flag
                    </div>
                    <Icon name='info-outlined' />
                  </div>
                }
              >
                {!hasVariants
                  ? 'Add at least one variant to start an experiment'
                  : 'Tag this feature as an experiment'}
              </Tooltip>
            </FormGroup>
          )}
          <FeatureSettingsTab
            identity={identity}
            projectId={projectId}
            projectFlag={projectFlag}
            onChange={onProjectFlagChange}
            onHasMetadataRequiredChange={onHasMetadataRequiredChange}
          />
        </>
      )}
    </>
  )
}

export default CreateFeatureTab
