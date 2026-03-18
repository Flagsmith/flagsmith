import React, { FC, useCallback, useEffect, useState } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValue from './FeatureValue'
import FeatureSettings from './FeatureSettings'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'
import { ProjectPermission } from 'common/types/permissions.types'
import Switch from 'components/Switch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import InfoMessage from 'components/InfoMessage'
import { useGetProjectQuery } from 'common/services/useProject'
import { useCreateTagMutation, useGetTagsQuery } from 'common/services/useTag'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  featureState: FeatureState
  overrideFeatureState?: FeatureState
  projectFlag: ProjectFlag | null
  featureContentType: any
  identity?: string
  defaultExperiment?: boolean
  onEnvironmentFlagChange: (changes: FeatureState) => void
  onProjectFlagChange: (changes: ProjectFlag) => void
  onRemoveMultivariateOption?: (id: number) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeature: FC<CreateFeatureTabProps> = ({
  defaultExperiment,
  error,
  featureContentType,
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
    permission: ProjectPermission.ADMIN,
  })

  const { data: project } = useGetProjectQuery({ id: projectId })
  const preventFlagDefaults = !!project?.prevent_flag_defaults && !identity

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
          const result = await createTag({
            projectId,
            tag: {
              color: '#6A52CF',
              description: 'Experiment flag',
              label: 'experiment',
            },
          }).unwrap()
          experimentTag = result
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
            tags: projectFlag.tags.filter((id) => id !== experimentTag!.id),
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
          {preventFlagDefaults && (
            <InfoMessage collapseId='create-flag'>
              This will create the feature for <strong>all environments</strong>
              , you can edit the feature's enabled state and value per
              environment once the feature is created.
            </InfoMessage>
          )}
          <FeatureValue
            error={error}
            createFeature={createFeature}
            hideValue={preventFlagDefaults}
            identity={identity}
            isEdit={!!identity}
            noPermissions={noPermissions}
            projectFlag={projectFlag}
            featureState={overrideFeatureState || featureState}
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
          <FeatureSettings
            projectAdmin={projectAdmin}
            createFeature={createFeature}
            featureContentType={featureContentType}
            identity={identity}
            isEdit={!!identity}
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

export default CreateFeature
