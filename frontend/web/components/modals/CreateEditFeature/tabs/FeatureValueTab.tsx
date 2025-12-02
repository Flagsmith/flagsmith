import React, { FC } from 'react'
import { ChangeRequest, ProjectFlag } from 'common/types/responses'
import { useGetProjectQuery } from 'common/services/useProject'
import Utils from 'common/utils/utils'
import FeatureInPipelineGuard from 'components/release-pipelines/FeatureInPipelineGuard'
import InfoMessage from 'components/InfoMessage'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import JSONReference from 'components/JSONReference'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'
import Tooltip from 'components/Tooltip'
import EditFeatureValue from 'components/modals/CreateEditFeature/EditFeatureValue'
import { useHasPermission } from 'common/providers/Permission'

type FeatureValueTabType = {
  projectId: number
  environmentId: string
  environmentFlag: any
  projectFlag: ProjectFlag | null | undefined
  isSaving: boolean
  invalid: boolean
  existingChangeRequest?: ChangeRequest
  error: any
  identity?: string
  identityName?: string
  description: string
  multivariate_options: any[]
  environmentVariations: any[]
  default_enabled: boolean
  initial_value: any
  identityVariations: any[]
  featureName: string
  onValueChange: (initial_value: any) => void
  onCheckedChange: (default_enabled: boolean) => void
  onIdentityVariationsChange: (identityVariations: any[]) => void
  removeVariation: (i: number) => void
  updateVariation: (i: number, e: any, environmentVariations: any[]) => void
  addVariation: () => void
  saveFeatureValue: () => void
}

const FeatureValueTab: FC<FeatureValueTabType> = ({
  addVariation,
  default_enabled,
  description,
  environmentFlag,
  environmentId,
  environmentVariations,
  error,
  existingChangeRequest,
  featureName,
  identity,
  identityName,
  identityVariations,
  initial_value,
  invalid,
  isSaving,
  multivariate_options,
  onCheckedChange,
  onIdentityVariationsChange,
  onValueChange,
  projectFlag,
  projectId,
  removeVariation,
  saveFeatureValue,
  updateVariation,
}) => {
  const { data: project } = useGetProjectQuery({
    id: `${projectId}`,
  })
  const environment = project?.environments.find(
    (v) => `${v.id}` === `${environmentId}`,
  )
  const isVersioned = !!environment?.use_v2_feature_versioning
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)

  const manageFeaturePermission = Utils.getManageFeaturePermission(is4Eyes)

  const { permission: hasManageFeaturePermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: manageFeaturePermission,
    tags: projectFlag?.tags,
  })

  const noPermissions = !hasManageFeaturePermission

  const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
    project?.total_features,
    project?.max_features_allowed,
  )
  if (!projectFlag || !environment) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  return (
    <>
      <FormGroup>
        {featureLimitAlert.percentage &&
          Utils.displayLimitAlert('features', featureLimitAlert.percentage)}
        <FeatureInPipelineGuard
          projectId={projectId}
          featureId={projectFlag?.id}
          renderFallback={(matchingReleasePipeline) => (
            <>
              <h5>Environment Value </h5>
              <InfoMessage title={`Feature in release pipeline`}>
                This feature is in <b>{matchingReleasePipeline?.name}</b>{' '}
                release pipeline and its value cannot be changed
              </InfoMessage>
            </>
          )}
        >
          <Tooltip
            title={
              <h5>
                Environment Value <Icon name='info-outlined' />
              </h5>
            }
            place='top'
          >
            {Constants.strings.ENVIRONMENT_OVERRIDE_DESCRIPTION(
              environment.name,
            )}
          </Tooltip>
          {identity && description && (
            <FormGroup className='mb-4 mt-2 mx-3'>{description}</FormGroup>
          )}
          <EditFeatureValue
            error={error}
            createFeature={hasManageFeaturePermission}
            hideValue={false}
            isEdit={true}
            identity={identity}
            identityName={identityName}
            noPermissions={noPermissions}
            multivariate_options={multivariate_options}
            environmentVariations={environmentVariations}
            featureState={{
              enabled: default_enabled,
              feature_state_value: initial_value,
              multivariate_feature_state_values: identityVariations,
            }}
            environmentFlag={environmentFlag}
            projectFlag={projectFlag}
            onChange={(featureState) => {
              if (featureState.enabled !== undefined) {
                onCheckedChange(featureState.enabled)
              }
              if (featureState.feature_state_value !== undefined) {
                onValueChange(featureState.feature_state_value)
              }
              if (featureState.multivariate_feature_state_values !== undefined) {
                onIdentityVariationsChange(
                  featureState.multivariate_feature_state_values,
                )
              }
            }}
            removeVariation={removeVariation}
            updateVariation={updateVariation}
            addVariation={addVariation}
          />
          <JSONReference
            showNamesButton
            title={'Feature'}
            json={projectFlag}
          />
          <JSONReference title={'Feature state'} json={environmentFlag} />
          <FlagValueFooter
            is4Eyes={is4Eyes}
            isVersioned={isVersioned}
            projectId={projectId}
            projectFlag={projectFlag}
            environmentId={environmentId}
            environmentName={environment.name ?? ''}
            isSaving={isSaving}
            featureName={featureName}
            isInvalid={invalid}
            existingChangeRequest={!!existingChangeRequest}
            onSaveFeatureValue={saveFeatureValue}
          />
        </FeatureInPipelineGuard>
      </FormGroup>
    </>
  )
}

export default FeatureValueTab
