import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValue from './FeatureValue'
import FeatureSettings from './FeatureSettings'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'
import {
  ADMIN_PERMISSION,
  ProjectPermission,
} from 'common/types/permissions.types'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  featureState: FeatureState
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
            isEdit={false}
            identity={identity}
            noPermissions={noPermissions}
            featureState={featureState}
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
            isEdit={false}
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
