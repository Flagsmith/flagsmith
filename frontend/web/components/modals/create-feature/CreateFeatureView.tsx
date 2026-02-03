import React, { FC } from 'react'
import classNames from 'classnames'
import FeatureLimitAlert from './FeatureLimitAlert'
import FeatureNameInput from './FeatureNameInput'
import CreateFeatureTab from './tabs/CreateFeature'
import FeatureUpdateSummary from './FeatureUpdateSummary'
import { FeatureState, ProjectFlag } from 'common/types/responses'

type CreateFeatureViewProps = {
  projectId: number
  projectFlag: Partial<ProjectFlag>
  environmentFlag: Partial<FeatureState>
  identityFlag?: FeatureState
  featureContentType: Record<string, any>
  identity?: string
  isEdit: boolean
  isSaving: boolean
  invalid: boolean
  regexValid: boolean
  caseSensitive?: boolean
  regex?: string
  featureLimitPercentage: number
  hasMetadataRequired: boolean
  providerError: any
  onProjectFlagChange: (changes: Partial<ProjectFlag>) => void
  onEnvironmentFlagChange: (changes: Partial<FeatureState>) => void
  onRemoveMultivariateOption: (id: number) => void
  onHasMetadataRequiredChange: (required: boolean) => void
  onCreateFeature: () => void
  parseError: (error: any) => { featureError: string; featureWarning: string }
}

const CreateFeatureView: FC<CreateFeatureViewProps> = ({
  caseSensitive,
  environmentFlag,
  featureContentType,
  featureLimitPercentage,
  hasMetadataRequired,
  identity,
  identityFlag,
  invalid,
  isEdit,
  isSaving,
  onCreateFeature,
  onEnvironmentFlagChange,
  onHasMetadataRequiredChange,
  onProjectFlagChange,
  onRemoveMultivariateOption,
  parseError,
  projectFlag,
  projectId,
  providerError,
  regex,
  regexValid,
}) => {
  return (
    <div className={classNames(!isEdit ? 'create-feature-tab px-3' : '')}>
      <FeatureLimitAlert projectId={projectId} onChange={() => {}} />
      <div className={identity ? 'px-3' : ''}>
        <FeatureNameInput
          value={projectFlag.name}
          onChange={(name) =>
            onProjectFlagChange({
              name,
            })
          }
          caseSensitive={caseSensitive}
          regex={regex}
          regexValid={regexValid}
          autoFocus
        />
      </div>
      <CreateFeatureTab
        projectId={projectId}
        error={providerError}
        featureState={environmentFlag as FeatureState}
        projectFlag={projectFlag as ProjectFlag}
        featureContentType={featureContentType}
        identity={identity}
        overrideFeatureState={
          identityFlag ? (environmentFlag as FeatureState) : undefined
        }
        onEnvironmentFlagChange={onEnvironmentFlagChange}
        onProjectFlagChange={onProjectFlagChange}
        onRemoveMultivariateOption={onRemoveMultivariateOption}
        onHasMetadataRequiredChange={onHasMetadataRequiredChange}
        featureError={parseError(providerError).featureError}
        featureWarning={parseError(providerError).featureWarning}
      />
      <FeatureUpdateSummary
        identity={identity}
        onCreateFeature={onCreateFeature}
        isSaving={isSaving}
        name={projectFlag.name}
        invalid={invalid}
        regexValid={regexValid}
        featureLimitPercentage={featureLimitPercentage}
        hasMetadataRequired={hasMetadataRequired}
      />
    </div>
  )
}

export default CreateFeatureView
