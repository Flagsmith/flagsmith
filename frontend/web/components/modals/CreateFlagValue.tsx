import React, { FC } from 'react'
import {
  FeatureState,
  MultivariateFeatureStateValue,
  MultivariateOption,
  Project,
  ProjectFlag,
} from 'common/types/responses'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import ExistingChangeRequestAlert from 'components/ExistingChangeRequestAlert'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import useRegexValid from 'common/useRegexValid'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'
import { useHasPermission } from 'common/providers/Permission'
import Feature from 'components/Feature'

export type CreateProjectFlagType = Omit<
  ProjectFlag,
  'created_date' | 'id' | 'uuid' | 'project'
> & {
  id?: number
  uuid?: string
  project?: number
}

export type CreateFeatureStateType = Pick<
  FeatureState,
  'enabled' | 'multivariate_feature_state_values' | 'feature_state_value'
> &
  Partial<FeatureState>

type CreateFlagValueType = {
  error?: any
  project: Project
  environmentApiKey: string
  projectFlag: CreateProjectFlagType
  setProjectFlag: (projectFlag: CreateProjectFlagType) => void
  identity?: string
  featureState: FeatureState
  setFeatureState: (featureState: FeatureState) => void
}

const CreateFlagValue: FC<CreateFlagValueType> = ({
  environmentApiKey,
  error,
  featureState,
  identity,
  project,
  projectFlag,
  setFeatureState,
  setProjectFlag,
}) => {
  const caseSensitive = project?.only_allow_lower_case_feature_names
  const regexValid = useRegexValid(projectFlag.name, project.feature_name_regex)
  const environment = project?.environments?.find(
    (environment) => environment.api_key === environmentApiKey,
  )
  const { permission: canManageFeatures } = useHasPermission({
    id: `${environmentApiKey || ''}`,
    level: 'environment',
    permission: Utils.getManageFeaturePermission(
      Utils.changeRequestsEnabled(
        environment?.minimum_change_request_approvals,
      ),
    ),
  })
  const { permission: canCreateFeature } = useHasPermission({
    id: `${project.id}`,
    level: 'project',
    permission: 'CREATE_FEATURE',
  })
  if (!environment) return null

  const isEdit = !!projectFlag?.id
  const onRef = (e: InstanceType<typeof InputGroup>) => {
    if (!isEdit) {
      setTimeout(() => {
        e?.focus()
      }, 500)
    }
  }
  const onNameChange = (e: InputEvent) => {
    const newName = Utils.safeParseEventValue(e).replace(/ /g, '_')
    setProjectFlag({
      ...projectFlag,
      name: caseSensitive ? newName.toLowerCase() : newName,
    })
  }

  const addVariation = () => {
    setProjectFlag({
      ...projectFlag,
      multivariate_options: projectFlag.multivariate_options.concat([
        {
          ...Utils.valueToFeatureState(''),
          default_percentage_allocation: 0,
        },
      ]),
    })
  }

  const removeVariation = (index: number) => {
    setProjectFlag({
      ...projectFlag,
      multivariate_options: projectFlag.multivariate_options
        .slice(0, index)
        .concat(projectFlag.multivariate_options.slice(index + 1)),
    })
  }

  const updateVariation = (
    index: number,
    multivariateOption: MultivariateOption,
    environmentVariations: MultivariateFeatureStateValue[],
  ) => {
    // Update environment weights
    onChangeVariations(environmentVariations)
    //Update project options with new values
    const multivariate_options = [...projectFlag.multivariate_options]
    multivariate_options[index] = multivariateOption
    setProjectFlag({
      ...projectFlag,
      multivariate_options,
    })
  }

  const onChangeVariations = (
    environmentVariations: MultivariateFeatureStateValue[],
  ) => {
    // Update environment weights
    setFeatureState({
      ...featureState,
      multivariate_feature_state_values: environmentVariations,
    })
  }
  const onValueChange = (e: InputEvent) => {
    const value = Utils.getTypedValue(Utils.safeParseEventValue(e))
    setFeatureState({
      ...featureState,
      feature_state_value: value,
    })
  }
  return (
    <>
      {isEdit && (
        <Tooltip
          title={
            <h5 className='mb-4'>
              Environment Value <Icon name='info-outlined' />
            </h5>
          }
          place='top'
        >
          {Constants.strings.ENVIRONMENT_OVERRIDE_DESCRIPTION(environment.name)}
        </Tooltip>
      )}
      {projectFlag.id && (
        <ExistingChangeRequestAlert
          className='mb-4'
          featureId={projectFlag.id}
          environmentId={environmentApiKey}
        />
      )}
      {!isEdit && (
        <FormGroup className='mb-4 mt-2'>
          <InputGroup
            ref={onRef}
            data-test='featureID'
            inputProps={{
              className: 'full-width',
              maxLength: Constants.forms.maxLength.FEATURE_ID,
              name: 'featureID',
              readOnly: isEdit,
            }}
            value={projectFlag?.name}
            onChange={onNameChange}
            isValid={!!projectFlag.name && regexValid}
            type='text'
            title={
              <>
                <Tooltip
                  title={
                    <Row>
                      <span className={'mr-1'}>{isEdit ? 'ID' : 'ID*'}</span>
                      <Icon name='info-outlined' />
                    </Row>
                  }
                >
                  The ID that will be used by SDKs to retrieve the feature value
                  and enabled state. This cannot be edited once the feature has
                  been created.
                </Tooltip>
                {!!project.feature_name_regex && !isEdit && (
                  <div className='mt-2'>
                    <InfoMessage>
                      This must conform to the regular expression{' '}
                      <pre>{project.feature_name_regex}</pre>
                    </InfoMessage>
                  </div>
                )}
              </>
            }
            placeholder='E.g. header_size'
          />
          <ErrorMessage error={error?.name?.[0]} />
        </FormGroup>
      )}
      {identity && projectFlag.description && (
        <FormGroup className='mb-4 mt-2 mx-3'>
          <InputGroup
            value={projectFlag.description}
            data-test='featureDesc'
            inputProps={{
              className: 'full-width',
              name: 'featureDesc',
              readOnly: true,
            }}
            type='text'
            title={identity ? 'Description' : 'Description (optional)'}
            placeholder='No description'
          />
        </FormGroup>
      )}
      {!project.prevent_flag_defaults && (
        <div
          className={`${
            identity && !projectFlag.description ? 'mt-4 mx-3' : ''
          } ${identity ? 'mx-3' : ''}`}
        >
          <Feature
            readOnly={!canManageFeatures}
            hide_from_client={!!featureState.hide_from_client}
            multivariate_options={projectFlag.multivariate_options}
            environmentVariations={
              featureState.multivariate_feature_state_values
            }
            isEdit={isEdit}
            error={error?.initial_value?.[0]}
            canCreateFeature={canCreateFeature}
            identity={!!identity}
            removeVariation={removeVariation}
            updateVariation={updateVariation}
            addVariation={addVariation}
            checked={featureState.enabled}
            value={featureState.feature_state_value}
            identityVariations={featureState.multivariate_feature_state_values}
            onChangeIdentityVariations={onChangeVariations}
            environmentFlag={featureState}
            projectFlag={projectFlag}
            onValueChange={onValueChange}
            onCheckedChange={onEnabledChange}
          />
        </div>
      )}
    </>
  )
}

export default CreateFlagValue
