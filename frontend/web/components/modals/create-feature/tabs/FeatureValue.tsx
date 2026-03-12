import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import ValueEditor from 'components/ValueEditor'
import Constants from 'common/constants'
import { VariationOptions } from 'components/mv/VariationOptions'
import { AddVariationButton } from 'components/mv/AddVariationButton'
import ErrorMessage from 'components/ErrorMessage'
import WarningMessage from 'components/WarningMessage'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import Switch from 'components/Switch'
import Utils from 'common/utils/utils'
import { FeatureState, ProjectFlag } from 'common/types/responses'

function isNegativeNumberString(str: any) {
  if (typeof Utils.getTypedValue(str) !== 'number') {
    return false
  }
  if (typeof str !== 'string') {
    return false
  }
  const num = parseFloat(str)
  return !isNaN(num) && num < 0
}

type EditFeatureValueProps = {
  error: any
  createFeature: boolean
  hideValue: boolean
  isEdit: boolean
  identity?: string
  identityName?: string
  noPermissions: boolean
  featureState: FeatureState
  projectFlag: ProjectFlag
  onEnvironmentFlagChange: (changes: FeatureState) => void
  onProjectFlagChange: (changes: ProjectFlag) => void
  onRemoveMultivariateOption?: (id: number) => void
}

/* eslint-disable sort-destructure-keys/sort-destructure-keys */
const FeatureValue: FC<EditFeatureValueProps> = ({
  createFeature,
  error,
  featureState,
  hideValue,
  identity,
  isEdit,
  noPermissions,
  onEnvironmentFlagChange,
  onProjectFlagChange,
  onRemoveMultivariateOption,
  projectFlag,
}) => {
  const default_enabled = featureState.enabled ?? false
  const initial_value = featureState.feature_state_value
  const multivariate_options = projectFlag.multivariate_options || []
  const environmentVariations =
    featureState.multivariate_feature_state_values ?? []
  const identityVariations =
    featureState.multivariate_feature_state_values ?? []

  const addVariation = () => {
    const newVariation = {
      ...Utils.valueToFeatureState(''),
      default_percentage_allocation: 0,
    }
    onProjectFlagChange({
      multivariate_options: [...multivariate_options, newVariation],
    })
  }

  const [isNegativeNumber, setIsNegativeNumber] = useState(
    isNegativeNumberString(featureState?.feature_state_value),
  )

  useEffect(() => {
    setIsNegativeNumber(
      isNegativeNumberString(featureState?.feature_state_value),
    )
  }, [featureState?.feature_state_value])

  const handleRemoveVariation = (i: number) => {
    const idToRemove = multivariate_options[i].id

    const doRemove = () => {
      if (idToRemove && onRemoveMultivariateOption) {
        onRemoveMultivariateOption(idToRemove)
      }
      const newMultivariateOptions = multivariate_options.filter(
        (_, index) => index !== i,
      )
      onProjectFlagChange({
        multivariate_options: newMultivariateOptions,
      })
    }

    if (idToRemove) {
      openConfirm({
        body: 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.',
        destructive: true,
        onYes: doRemove,
        title: 'Delete variation',
        yesText: 'Confirm',
      })
    } else {
      doRemove()
    }
  }

  const handleUpdateVariation = (
    i: number,
    updatedVariation: any,
    updatedEnvironmentVariations: any[],
  ) => {
    // Update the environment variations (weights)
    onEnvironmentFlagChange({
      multivariate_feature_state_values: updatedEnvironmentVariations,
    })

    // Update the multivariate option itself
    const newMultivariateOptions = [...multivariate_options]
    newMultivariateOptions[i] = updatedVariation
    onProjectFlagChange({
      multivariate_options: newMultivariateOptions,
    })
  }

  const enabledString = isEdit ? 'Enabled' : 'Enabled by default'
  const controlPercentage = Utils.calculateControl(multivariate_options)

  const getValueString = () => {
    if (multivariate_options && multivariate_options.length) {
      return `Control Value - ${controlPercentage}%`
    }
    return 'Value'
  }
  const valueString = getValueString()

  const showValue = !(
    !!identity &&
    multivariate_options &&
    !!multivariate_options.length
  )

  return (
    <>
      {!hideValue && (
        <div className={`${identity ? 'mx-3' : ''}`}>
          <FormGroup className='mb-4'>
            <Tooltip
              title={
                <div className='flex-row'>
                  <Switch
                    data-test='toggle-feature-button'
                    defaultChecked={default_enabled}
                    disabled={noPermissions}
                    checked={default_enabled}
                    onChange={(enabled) => onEnvironmentFlagChange({ enabled })}
                    className='ml-0'
                  />
                  <div className='label-switch ml-3 mr-1'>
                    {enabledString || 'Enabled'}
                  </div>
                  {!isEdit && <Icon name='info-outlined' />}
                </div>
              }
            >
              {!isEdit
                ? 'This will determine the initial enabled state for all environments. You can edit the this individually for each environment once the feature is created.'
                : ''}
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
                    value={`${
                      typeof initial_value === 'undefined' ||
                      initial_value === null
                        ? ''
                        : initial_value
                    }`}
                    onChange={(e: any) => {
                      const feature_state_value = Utils.getTypedValue(
                        Utils.safeParseEventValue(e),
                      )
                      onEnvironmentFlagChange({ feature_state_value })
                    }}
                    disabled={noPermissions}
                    placeholder="e.g. 'big' "
                  />
                }
                tooltip={`${Constants.strings.REMOTE_CONFIG_DESCRIPTION}${
                  !isEdit
                    ? '<br/>Setting this when creating a feature will set the value for all environments. You can edit this individually for each environment once the feature is created.'
                    : ''
                }`}
                title={`${valueString}`}
              />
            </FormGroup>
          )}

          {isNegativeNumber && (
            <WarningMessage
              warningMessage={
                <div>
                  This feature currently has the value of{' '}
                  <strong>"{featureState.feature_state_value}"</strong>. Saving
                  this feature will convert its value from a string to a number.
                  If you wish to preserve this value as a string, please save it
                  using the{' '}
                  <a href='https://api.flagsmith.com/api/v1/docs/#/api/api_v1_environments_featurestates_update'>
                    API
                  </a>
                  .
                </div>
              }
            />
          )}

          {!!error?.initial_value?.[0] && (
            <div className='mx-2 mt-2'>
              <ErrorMessage error={error.initial_value[0]} />
            </div>
          )}

          {!!identity && (
            <div>
              <FormGroup className='mb-4'>
                <VariationOptions
                  disabled
                  select
                  controlValue={
                    projectFlag.environment_feature_state
                      ?.feature_state_value ?? null
                  }
                  controlPercentage={controlPercentage}
                  variationOverrides={identityVariations}
                  setVariations={(multivariate_feature_state_values) =>
                    onEnvironmentFlagChange({
                      multivariate_feature_state_values,
                    })
                  }
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
                {(!!environmentVariations || !isEdit) && (
                  <VariationOptions
                    canCreateFeature={createFeature}
                    disabled={!!identity || noPermissions}
                    controlValue={featureState.feature_state_value}
                    controlPercentage={controlPercentage}
                    variationOverrides={environmentVariations}
                    updateVariation={handleUpdateVariation}
                    weightTitle={
                      isEdit ? 'Environment Weight %' : 'Default Weight %'
                    }
                    multivariateOptions={multivariate_options}
                    removeVariation={handleRemoveVariation}
                  />
                )}
              </FormGroup>
              {Utils.renderWithPermission(
                createFeature,
                Constants.projectPermissions('Create Feature'),
                <AddVariationButton
                  multivariateOptions={multivariate_options}
                  disabled={!createFeature || noPermissions}
                  onClick={addVariation}
                />,
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}

export default FeatureValue
