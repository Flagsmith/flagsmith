import React from 'react'
import ValueEditor from 'components/ValueEditor'
import Constants from 'common/constants'
import Icon from 'components/icons/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import shallowEqual from 'fbjs/lib/shallowEqual'
import { ProjectPermission } from 'common/types/permissions.types'
import { VariationKeyLabel } from './VariationKeyLabel'

interface VariationValueProps {
  canCreateFeature: boolean
  disabled: boolean
  index: number
  onChange: (value: any) => void
  onRemove?: () => void
  readOnly: boolean
  siblingKeys: (string | null | undefined)[]
  value: any
  weightTitle: string
}

export const VariationValueInput: React.FC<VariationValueProps> = ({
  canCreateFeature,
  disabled,
  index,
  onChange,
  onRemove,
  readOnly,
  siblingKeys,
  value,
  weightTitle,
}) => {
  return (
    <div className='mb-2'>
      <VariationKeyLabel
        value={value.key}
        index={index}
        disabled={disabled || !canCreateFeature}
        readOnly={readOnly}
        siblingKeys={siblingKeys}
        onChange={(key) => onChange({ ...value, key })}
      />
      <Row className='align-items-start'>
        <div className='flex flex-1 overflow-hidden'>
          <InputGroup
            noMargin
            component={
              <>
                {Utils.renderWithPermission(
                  canCreateFeature,
                  readOnly
                    ? 'Variation values are defined at the feature level and cannot be changed per segment.'
                    : Constants.projectPermissions(
                        ProjectPermission.CREATE_FEATURE,
                      ),
                  <ValueEditor
                    data-test={`featureVariationValue${
                      Utils.featureStateToValue(value) || index
                    }`}
                    name='featureValue'
                    className='full-width code-medium'
                    value={Utils.getTypedValue(
                      Utils.featureStateToValue(value),
                    )}
                    disabled={!canCreateFeature || disabled || readOnly}
                    onBlur={() => {
                      const newValue = {
                        ...value,
                        // Trim spaces and do conversion on blur
                        ...Utils.valueToFeatureState(
                          Utils.featureStateToValue(value),
                        ),
                      }
                      if (!shallowEqual(newValue, value)) {
                        //occurs if we converted a trimmed value
                        onChange(newValue)
                      }
                    }}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      onChange({
                        ...value,
                        ...Utils.valueToFeatureState(
                          Utils.safeParseEventValue(e),
                          false,
                        ),
                      })
                    }}
                    placeholder="e.g. 'big' "
                  />,
                )}
              </>
            }
            tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
            title='Variation Value'
          />
        </div>
        <div className='ml-3' style={{ width: 160 }}>
          <InputGroup
            type='number'
            data-test={`featureVariationWeight${Utils.featureStateToValue(
              value,
            )}`}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              const val = Utils.safeParseEventValue(e)
              onChange({
                ...value,
                default_percentage_allocation: val ? parseFloat(val) : null,
              })
            }}
            value={value.default_percentage_allocation}
            inputProps={{
              readOnly: disabled,
              step: 'any',
            }}
            title={weightTitle}
          />
        </div>
        {!!onRemove && !readOnly && (
          <div style={{ top: '27px' }} className='ml-2 position-relative'>
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
    </div>
  )
}
