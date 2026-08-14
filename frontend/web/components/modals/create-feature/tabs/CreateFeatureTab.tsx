import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValueTab from './FeatureValueTab'
import FeatureSettingsTab from './FeatureSettingsTab'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'
import { ProjectPermission } from 'common/types/permissions.types'
import InfoMessage from 'components/InfoMessage'
import { useGetProjectQuery } from 'common/services/useProject'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  featureState: FeatureState
  overrideFeatureState?: FeatureState
  projectFlag: ProjectFlag | null
  identity?: string
  ownerIds?: number[]
  groupOwnerIds?: number[]
  onOwnerIdsChange?: (ids: number[]) => void
  onGroupOwnerIdsChange?: (ids: number[]) => void
  onEnvironmentFlagChange: (changes: Partial<FeatureState>) => void
  onProjectFlagChange: (changes: Partial<ProjectFlag>) => void
  onRemoveMultivariateOption?: (id: number) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeatureTab: FC<CreateFeatureTabProps> = ({
  error,
  featureError,
  featureState,
  featureWarning,
  groupOwnerIds,
  identity,
  onEnvironmentFlagChange,
  onGroupOwnerIdsChange,
  onHasMetadataRequiredChange,
  onOwnerIdsChange,
  onProjectFlagChange,
  onRemoveMultivariateOption,
  overrideFeatureState,
  ownerIds,
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
          <FeatureValueTab
            error={error}
            projectId={projectId}
            identity={identity}
            noPermissions={noPermissions}
            projectFlag={projectFlag}
            featureState={overrideFeatureState || featureState}
            onEnvironmentFlagChange={onEnvironmentFlagChange}
            onProjectFlagChange={onProjectFlagChange}
            onRemoveMultivariateOption={onRemoveMultivariateOption}
          />
          <FeatureSettingsTab
            identity={identity}
            projectId={projectId}
            projectFlag={projectFlag}
            ownerIds={ownerIds}
            groupOwnerIds={groupOwnerIds}
            onOwnerIdsChange={onOwnerIdsChange}
            onGroupOwnerIdsChange={onGroupOwnerIdsChange}
            onChange={onProjectFlagChange}
            onHasMetadataRequiredChange={onHasMetadataRequiredChange}
          />
        </>
      )}
    </>
  )
}

export default CreateFeatureTab
