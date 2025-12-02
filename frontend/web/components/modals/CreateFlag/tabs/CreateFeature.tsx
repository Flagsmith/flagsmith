import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import FeatureValue from 'components/modals/CreateFlag/tabs/FeatureValue'
import FeatureSettings from 'components/modals/CreateFlag/tabs/FeatureSettings'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import { useHasPermission } from 'common/providers/Permission'

type CreateFeatureTabProps = {
  projectId: number
  error: any
  multivariate_options: any[]
  environmentVariations: any[]
  featureState: Partial<FeatureState>
  environmentFlag: any
  projectFlag: ProjectFlag | null | undefined
  featureContentType: any
  identity?: string
  tags: number[]
  description: string
  is_server_key_only: boolean
  is_archived: boolean
  onChange: (featureState: Partial<FeatureState>) => void
  removeVariation: (i: number) => void
  updateVariation: (i: number, e: any, environmentVariations: any[]) => void
  addVariation: () => void
  onTagsChange: (tags: number[]) => void
  onMetadataChange: (metadata: any[]) => void
  onDescriptionChange: (description: string) => void
  onServerKeyOnlyChange: (is_server_key_only: boolean) => void
  onArchivedChange: (is_archived: boolean) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  featureError?: string
  featureWarning?: string
}

const CreateFeature: FC<CreateFeatureTabProps> = ({
  addVariation,
  description,
  environmentFlag,
  environmentVariations,
  error,
  featureContentType,
  featureError,
  featureState,
  featureWarning,
  identity,
  is_archived,
  is_server_key_only,
  multivariate_options,
  onArchivedChange,
  onChange,
  onDescriptionChange,
  onHasMetadataRequiredChange,
  onMetadataChange,
  onServerKeyOnlyChange,
  onTagsChange,
  projectFlag,
  projectId,
  removeVariation,
  tags,
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
      <FeatureValue
        error={error}
        createFeature={createFeature}
        hideValue={false}
        isEdit={false}
        noPermissions={noPermissions}
        multivariate_options={multivariate_options}
        environmentVariations={environmentVariations}
        featureState={featureState}
        environmentFlag={environmentFlag}
        projectFlag={projectFlag!}
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
        tags={tags}
        description={description}
        is_server_key_only={is_server_key_only}
        is_archived={is_archived}
        onTagsChange={onTagsChange}
        onMetadataChange={onMetadataChange}
        onDescriptionChange={onDescriptionChange}
        onServerKeyOnlyChange={onServerKeyOnlyChange}
        onArchivedChange={onArchivedChange}
        onHasMetadataRequiredChange={onHasMetadataRequiredChange}
      />
    </>
  )
}

export default CreateFeature
