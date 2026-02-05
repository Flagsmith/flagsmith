import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValue from './FeatureValue'
import FeatureSettings from './FeatureSettings'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  featureState: FeatureState
  overrideFeatureState?: FeatureState
  projectFlag: ProjectFlag | null
  featureContentType: any
  identity?: string
  onEnvironmentFlagChange: (changes: FeatureState) => void
  onProjectFlagChange: (changes: ProjectFlag) => void
  onRemoveMultivariateOption?: (id: number) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeature: FC<CreateFeatureTabProps> = ({
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
    permission: 'CREATE_FEATURE',
  })

  const { permission: projectAdmin } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'ADMIN',
  })

  const noPermissions = !createFeature && !projectAdmin

  return (
    <>
      <ErrorMessage error={featureError} />
      <WarningMessage warningMessage={featureWarning} />
      {!!projectFlag && (
        <>
          <FeatureValue
            error={error}
            createFeature={createFeature}
            hideValue={false}
            isEdit={!!identity}
            identity={identity}
            noPermissions={noPermissions}
            featureState={overrideFeatureState || featureState}
            projectFlag={projectFlag}
            onEnvironmentFlagChange={onEnvironmentFlagChange}
            onProjectFlagChange={onProjectFlagChange}
            onRemoveMultivariateOption={onRemoveMultivariateOption}
          />
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
