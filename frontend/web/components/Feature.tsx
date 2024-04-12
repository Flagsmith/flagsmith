import React, { FunctionComponent } from 'react'
import ValueEditor from './ValueEditor'
import Constants from 'common/constants'
import VariationOptions from './mv/VariationOptions'
import AddVariationButton from './mv/AddVariationButton'
import ErrorMessage from './ErrorMessage'
import Tooltip from './Tooltip'
import Icon from './Icon'
import Utils from 'common/utils/utils'
import Switch from './Switch'
import InputGroup from './base/forms/InputGroup'
import {
  FeatureState,
  MultivariateFeatureStateValue,
  MultivariateOption,
  ProjectFlag
} from "common/types/responses";

interface FeatureProps {
  checked: boolean
  environmentFlag: FeatureState // Define the type of environmentFlag
  environmentVariations: any[] // Define the type of environmentVariations
  error: string
  hide_from_client: boolean
  identity: boolean
  isEdit: boolean
  multivariate_options: MultivariateOption[]
  onCheckedChange: () => void
  onValueChange: (value: string) => void
  projectFlag: ProjectFlag
  readOnly: boolean
  value: string
  removeVariation: (index: number) => void
  identityVariations?: MultivariateFeatureStateValue[]
  onChangeIdentityVariations: (variations: any[]) => void
  updateVariation: () => void
  canCreateFeature: boolean
  hideAddVariation?: boolean
  addVariation: () => void
}

const Feature: FunctionComponent<FeatureProps> = ({
  addVariation,
  canCreateFeature,
  checked,
  environmentFlag,
  environmentVariations,
  error,
  hide_from_client,
  hideAddVariation,
  identity,
  identityVariations,
  isEdit,
  multivariate_options,
  onChangeIdentityVariations,
  onCheckedChange,
  onValueChange,
  projectFlag,
  readOnly,
  removeVariation,
  updateVariation,
  value,
}) => {
  const enabledString = isEdit ? 'Enabled' : 'Enabled by default'
  const disabled = hide_from_client
  const controlPercentage = Utils.calculateControl(multivariate_options)
  const valueString = identity
    ? 'User override'
    : !!multivariate_options && multivariate_options.length
    ? `Control Value - ${controlPercentage}%`
    : `Value (optional)`

  const showValue =
    !identity && multivariate_options && !!multivariate_options.length

  return (
    <div>
      <FormGroup className='mb-4'>
        <Tooltip
          title={
            <div className='flex-row'>
              <Switch
                data-test='toggle-feature-button'
                defaultChecked={checked}
                disabled={disabled || readOnly}
                checked={!disabled && checked}
                onChange={onCheckedChange}
                className='ml-0'
              />
              <div className='label-switch ml-3 mr-1'>
                {enabledString || 'Enabled'}
              </div>
              {!isEdit && <Icon name='info-outlined' />}
            </div>
          }
        >
          {!isEdit &&
            'This will determine the initial enabled state for all environments. You can edit the this individually for each environment once the feature is created.'}
        </Tooltip>
      </FormGroup>

      {showValue && (
        <FormGroup className='mb-4'>
          <InputGroup
            component={
              <ValueEditor
                data-test='featureValue'
                name='featureValue'
                className='full-width'
                value={
                  typeof value === 'undefined' || value === null ? '' : value
                }
                onChange={onValueChange}
                disabled={hide_from_client || readOnly}
                placeholder="e.g. 'big' "
              />
            }
            tooltip={`${Constants.strings.REMOTE_CONFIG_DESCRIPTION}${
              !isEdit
                ? '<br/>Setting this when creating a feature will set the value for all environments. You can edit the this individually for each environment once the feature is created.'
                : ''
            }`}
            title={`${valueString}`}
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
              controlValue={environmentFlag?.feature_state_value}
              controlPercentage={controlPercentage}
              variationOverrides={identityVariations}
              setVariations={onChangeIdentityVariations}
              updateVariation={() => {}}
              weightTitle='Override Weight %'
              projectFlag={projectFlag}
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
                disabled={!!identity || readOnly}
                controlValue={environmentFlag?.feature_state_value}
                controlPercentage={controlPercentage}
                variationOverrides={environmentVariations}
                updateVariation={updateVariation}
                weightTitle={
                  isEdit ? 'Environment Weight %' : 'Default Weight %'
                }
                multivariateOptions={multivariate_options}
                removeVariation={removeVariation}
              />
            ) : null}
          </FormGroup>
          {!hideAddVariation &&
            Utils.renderWithPermission(
              canCreateFeature,
              Constants.projectPermissions('Create Feature'),
              <AddVariationButton
                multivariateOptions={multivariate_options}
                disabled={!canCreateFeature || readOnly}
                onClick={addVariation}
              />,
            )}
        </div>
      )}
    </div>
  )
}

export default Feature
