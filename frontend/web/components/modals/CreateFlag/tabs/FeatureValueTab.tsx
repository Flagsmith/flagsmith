import { FC } from 'react'
import { ChangeRequest, ProjectFlag } from 'common/types/responses'
import { useGetProjectQuery } from 'common/services/useProject'
import Utils from 'common/utils/utils'
import FeatureInPipelineGuard from 'components/release-pipelines/FeatureInPipelineGuard'
import InfoMessage from 'components/InfoMessage'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import JSONReference from 'components/JSONReference'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'

type FeatureValueTabType = {
  projectId: number
  environmentId: string
  environmentFlag: any
  projectFlag: ProjectFlag | null | undefined
  isSaving: boolean
  isEdit: boolean
  isVersioned: boolean
  invalid: boolean
  existingChangeRequest?: ChangeRequest
}

const FeatureValueTab: FC<FeatureValueTabType> = ({
  environmentId,
  isEdit,
  projectFlag,
  projectId,
}) => {
  const { data: project } = useGetProjectQuery({
    id: `${projectId}`,
  })
  const environment = project?.environments.find((v) => v.id === environmentId)
  const is4Eyes =
    !!environment &&
    Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)

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

          {Value(error, projectAdmin, createFeature)}

          {isEdit && (
            <>
              <JSONReference
                showNamesButton
                title={'Feature'}
                json={projectFlag}
              />
              <JSONReference
                title={'Feature state'}
                json={this.props.environmentFlag}
              />
            </>
          )}
          <FlagValueFooter
            is4Eyes={is4Eyes}
            isVersioned={isVersioned}
            projectId={this.props.projectId}
            projectFlag={projectFlag}
            environmentId={this.props.environmentId}
            environmentName={
              _.find(project.environments, {
                api_key: this.props.environmentId,
              }).name ?? ''
            }
            isSaving={isSaving}
            featureName={this.state.name}
            isInvalid={invalid}
            existingChangeRequest={existingChangeRequest}
            onSaveFeatureValue={saveFeatureValue}
            identity={identity}
          />
        </FeatureInPipelineGuard>
      </FormGroup>
    </>
  )
}

export default FeatureValueTab
