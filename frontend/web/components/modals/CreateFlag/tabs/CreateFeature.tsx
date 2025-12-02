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
  multivariate_options: any[]
  environmentVariations: any[]
  featureState: FeatureState
  environmentFlag: any
  projectFlag: ProjectFlag | null
  featureContentType: any
  identity?: string
  onChange: (featureState: FeatureState) => void
  onProjectFlagChange: (projectFlag: ProjectFlag) => void
  removeVariation: (i: number) => void
  updateVariation: (i: number, e: any, environmentVariations: any[]) => void
  addVariation: () => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeature: FC<CreateFeatureTabProps> = ({
  addVariation,
  environmentFlag,
  environmentVariations,
  error,
  featureContentType,
  featureError,
  featureState,
  featureWarning,
  identity,
  multivariate_options,
  onChange,
  onHasMetadataRequiredChange,
  onProjectFlagChange,
  projectFlag,
  projectId,
  removeVariation,
  updateVariation,
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
            isEdit={false}
            identity={identity}
            noPermissions={noPermissions}
            multivariate_options={multivariate_options}
            environmentVariations={environmentVariations}
            featureState={featureState}
            environmentFlag={environmentFlag}
            projectFlag={projectFlag}
            onChange={onChange}
            removeVariation={removeVariation}
            updateVariation={updateVariation}
            addVariation={addVariation}
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
