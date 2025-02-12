import React from 'react'
import ValueEditor from 'components/ValueEditor' // we need this to make JSX compile
import Constants from 'common/constants'
import Icon from 'components/Icon'
import shallowEqual from 'fbjs/lib/shallowEqual'

const VariationValue = ({
  disabled,
  index,
  onChange,
  onRemove,
  readOnlyValue,
  value,
  weightTitle,
}) => (
  <Row className='align-items-start mb-2'>
    <div className='flex flex-1 overflow-hidden'>
      <InputGroup
        noMargin
        component={
          <ValueEditor
            data-test={`featureVariationValue${
              Utils.featureStateToValue(value) || index
            }`}
            name='featureValue'
            className='full-width code-medium'
            value={Utils.getTypedValue(Utils.featureStateToValue(value))}
            disabled={disabled || readOnlyValue}
            onBlur={() => {
              const newValue = {
                ...value,
                // Trim spaces and do conversion on blur
                ...Utils.valueToFeatureState(Utils.featureStateToValue(value)),
              }
              if (!shallowEqual(newValue, value)) {
                //occurs if we converted a trimmed value
                onChange(newValue)
              }
            }}
            onChange={(e) => {
              onChange({
                ...value,
                ...Utils.valueToFeatureState(
                  Utils.safeParseEventValue(e),
                  false,
                ),
              })
            }}
            placeholder="e.g. 'big' "
          />
        }
        tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
        title='Variation Value'
      />
    </div>
    <div className='ml-3' style={{ width: 160 }}>
      <InputGroup
        type='text'
        data-test={`featureVariationWeight${Utils.featureStateToValue(value)}`}
        onChange={(e) => {
          onChange({
            ...value,
            default_percentage_allocation: Utils.safeParseEventValue(e)
              ? parseInt(Utils.safeParseEventValue(e))
              : null,
          })
        }}
        value={value.default_percentage_allocation}
        inputProps={{
          maxLength: 3,
          readOnly: disabled,
        }}
        title={weightTitle}
      />
    </div>
    {!!onRemove && (
      <div style={{ position: 'relative', top: '27px' }} className='ml-2'>
        <button
          onClick={onRemove}
          id='delete-multivariate'
          type='button'
          className='btn btn-with-icon'
        >
          <Icon name='trash-2' width={20} fill={'#656D7B'} />
        </button>
      </div>
    )}
  </Row>
)

export default VariationValue
