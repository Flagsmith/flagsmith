// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import ValueEditor from './ValueEditor'
import Constants from 'common/constants'
import VariationOptions from './mv/VariationOptions'
import AddVariationButton from './mv/AddVariationButton'
import ErrorMessage from './ErrorMessage'
import Tooltip from './Tooltip'
import Icon from './Icon'

export default class Feature extends PureComponent {
  static displayName = 'Feature'

  removeVariation = (i) => {
    const idToRemove = this.props.multivariate_options[i].id

    if (idToRemove) {
      openConfirm({
        body: 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.',
        destructive: true,
        onYes: () => {
          this.props.removeVariation(i)
        },
        title: 'Delete variation',
        yesText: 'Confirm',
      })
    } else {
      this.props.removeVariation(i)
    }
  }

  render() {
    const {
      checked,
      environmentFlag,
      environmentVariations,
      error,
      identity,
      isEdit,
      multivariate_options,
      onCheckedChange,
      onValueChange,
      projectFlag,
      readOnly,
      value,
    } = this.props

    const enabledString = isEdit ? 'Enabled' : 'Enabled by default'
    const controlPercentage = Utils.calculateControl(multivariate_options)
    const valueString = identity
      ? 'User override'
      : !!multivariate_options && multivariate_options.length
      ? `Control Value - ${controlPercentage}%`
      : `Value (optional)`

    const showValue = !(
      !!identity &&
      multivariate_options &&
      !!multivariate_options.length
    )
    return (
      <div>
        <FormGroup className='mb-4'>
          <Tooltip
            title={
              <div className='flex-row'>
                <Switch
                  data-test='toggle-feature-button'
                  defaultChecked={checked}
                  disabled={readOnly}
                  checked={checked}
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
                  value={`${
                    typeof value === 'undefined' || value === null ? '' : value
                  }`}
                  onChange={onValueChange}
                  disabled={readOnly}
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
                variationOverrides={this.props.identityVariations}
                setVariations={this.props.onChangeIdentityVariations}
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
                  disabled={!!identity || readOnly}
                  controlValue={environmentFlag?.feature_state_value}
                  controlPercentage={controlPercentage}
                  variationOverrides={environmentVariations}
                  updateVariation={this.props.updateVariation}
                  weightTitle={
                    isEdit ? 'Environment Weight %' : 'Default Weight %'
                  }
                  multivariateOptions={multivariate_options}
                  removeVariation={this.removeVariation}
                />
              )}
            </FormGroup>
            {!this.props.hideAddVariation &&
              Utils.renderWithPermission(
                this.props.canCreateFeature,
                Constants.projectPermissions('Create Feature'),
                <AddVariationButton
                  multivariateOptions={multivariate_options}
                  disabled={!this.props.canCreateFeature || readOnly}
                  onClick={this.props.addVariation}
                />,
              )}
          </div>
        )}
      </div>
    )
  }
}
