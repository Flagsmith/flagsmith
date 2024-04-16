import React, { FC, useRef } from 'react'
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
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Tooltip from 'components/Tooltip'
import Switch from 'components/Switch'
import ValueEditor from 'components/ValueEditor'
import VariationOptions from 'components/mv/VariationOptions'
import AddVariationButton from 'components/mv/AddVariationButton'

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
  featureState: CreateFeatureStateType
  setFeatureState: (featureState: CreateFeatureStateType) => void
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
  const { data: environments } = useGetEnvironmentsQuery({
    projectId: `${project.id}`,
  })
  const environment = environments?.results?.find(
    (env) => env.api_key === environmentApiKey,
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
  const focused = useRef(false)
  const isEdit = !!projectFlag?.id
  const onRef = (e: InstanceType<typeof InputGroup>) => {
    if (focused.current) return
    focused.current = true
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
  const onValueChange = (e: string) => {
    const value = Utils.getTypedValue(Utils.safeParseEventValue(e))
    setFeatureState({
      ...featureState,
      feature_state_value: value,
    })
  }
  const onEnabledChange = () => {
    setFeatureState({
      ...featureState,
      enabled: !featureState.enabled,
    })
  }
  const environmentVariations = featureState.multivariate_feature_state_values
  const enabledString = isEdit ? 'Enabled' : 'Enabled by default'
  const controlPercentage = Utils.calculateControl(
    projectFlag.multivariate_options,
  )
  const hideValue = !!identity && !!projectFlag.multivariate_options.length
  const valueTitle = identity
    ? 'User override'
    : projectFlag.multivariate_options.length
    ? `Control Value - ${controlPercentage}%`
    : `Value (optional)`

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
          <div>
            <FormGroup className='mb-4'>
              <Tooltip
                title={
                  <div className='flex-row'>
                    <Switch
                      data-test='toggle-feature-button'
                      defaultChecked={featureState.enabled}
                      disabled={!canManageFeatures}
                      checked={featureState.enabled}
                      onChange={onEnabledChange}
                      className='ml-0'
                    />
                    <div className='label-switch ml-3 mr-1'>
                      {enabledString}
                    </div>
                    {!isEdit && <Icon name='info-outlined' />}
                  </div>
                }
              >
                {!isEdit &&
                  'This will determine the initial enabled state for all environments. You can edit the this individually for each environment once the feature is created.'}
              </Tooltip>
            </FormGroup>

            {!hideValue && (
              <FormGroup className='mb-4'>
                <InputGroup
                  component={
                    <ValueEditor
                      data-test='featureValue'
                      name='featureValue'
                      className='full-width'
                      value={
                        typeof featureState.feature_state_value ===
                          'undefined' ||
                        featureState.feature_state_value === null
                          ? ''
                          : featureState.feature_state_value
                      }
                      onChange={onValueChange}
                      disabled={!canManageFeatures}
                      placeholder="e.g. 'big' "
                    />
                  }
                  tooltip={`${Constants.strings.REMOTE_CONFIG_DESCRIPTION}${
                    !isEdit
                      ? '<br/>Setting this when creating a feature will set the value for all environments. You can edit the this individually for each environment once the feature is created.'
                      : ''
                  }`}
                  title={`${valueTitle}`}
                />
              </FormGroup>
            )}

            {!!error && (
              <div className='mx-2 mt-2'>
                <ErrorMessage error={error} />
              </div>
            )}
            {!!identity && (
              <div>
                <FormGroup className='mb-4'>
                  <VariationOptions
                    disabled
                    select
                    controlValue={featureState?.feature_state_value}
                    controlPercentage={controlPercentage}
                    variationOverrides={
                      featureState.multivariate_feature_state_values
                    }
                    setVariations={onChangeVariations}
                    updateVariation={() => {}}
                    weightTitle='Override Weight %'
                    multivariateOptions={projectFlag.multivariate_options}
                    removeVariation={() => {}}
                  />
                </FormGroup>
              </div>
            )}
            {!identity && (
              <div>
                <FormGroup className='mb-0'>
                  {!!environmentVariations || !isEdit ? (
                    <VariationOptions
                      setVariations={onChangeVariations}
                      disabled={!!identity || !canManageFeatures}
                      controlValue={featureState.feature_state_value}
                      controlPercentage={controlPercentage}
                      variationOverrides={environmentVariations}
                      updateVariation={updateVariation}
                      weightTitle={
                        isEdit ? 'Environment Weight %' : 'Default Weight %'
                      }
                      multivariateOptions={projectFlag.multivariate_options}
                      removeVariation={removeVariation}
                    />
                  ) : null}
                </FormGroup>
                {Utils.renderWithPermission(
                  canCreateFeature,
                  Constants.projectPermissions('Create Feature'),
                  <AddVariationButton
                    multivariateOptions={projectFlag.multivariate_options}
                    disabled={!canCreateFeature || !canManageFeatures}
                    onClick={addVariation}
                  />,
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default CreateFlagValue
