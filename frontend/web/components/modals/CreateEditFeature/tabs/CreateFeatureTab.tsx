import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import EditFeatureValue from 'components/modals/CreateEditFeature/EditFeatureValue'
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
  onChange: (featureState: Partial<FeatureState>) => void
  removeVariation: (i: number) => void
  updateVariation: (i: number, e: any, environmentVariations: any[]) => void
  addVariation: () => void
  Settings: (
    projectAdmin: boolean,
    createFeature: boolean,
    featureContentType: any,
  ) => JSX.Element
  featureError?: string
  featureWarning?: string
}

const CreateFeatureTab: FC<CreateFeatureTabProps> = ({
  Settings,
  addVariation,
  environmentFlag,
  environmentVariations,
  error,
  featureContentType,
  featureError,
  featureState,
  featureWarning,
  multivariate_options,
  onChange,
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
      <EditFeatureValue
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
      {Settings(projectAdmin, createFeature, featureContentType)}
    </>
  )
}

export default CreateFeatureTab
