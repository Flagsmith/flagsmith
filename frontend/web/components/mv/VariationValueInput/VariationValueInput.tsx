import React from 'react'
import ValueEditor from 'components/ValueEditor'
import ErrorMessage from 'components/ErrorMessage'
import Constants from 'common/constants'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import shallowEqual from 'fbjs/lib/shallowEqual'
import { ProjectPermission } from 'common/types/permissions.types'
import { colorIconSecondary } from 'common/theme/tokens'
import { VariationKeyLabel } from 'components/mv/VariationKeyLabel'
import './VariationValueInput.scss'

interface VariationValueProps {
  apiError?: string | null
  canCreateFeature: boolean
  disabled: boolean
  index: number
  onChange: (value: any) => void
  onRemove?: () => void
  readOnly: boolean
  siblingKeys: (string | null | undefined)[]
  unsaved?: boolean
  value: any
  weightTitle: string
}

export const VariationValueInput: React.FC<VariationValueProps> = ({
  apiError,
  canCreateFeature,
  disabled,
  index,
  onChange,
  onRemove,
  readOnly,
  siblingKeys,
  unsaved,
  value,
  weightTitle,
}) => {
  return (
    <div className='variant-card rounded border-1 shadow-sm p-3 mb-3'>
      <Row className='justify-content-between align-items-start mb-3'>
        <VariationKeyLabel
          value={value.key}
          index={index}
          disabled={disabled || !canCreateFeature}
          readOnly={readOnly}
          siblingKeys={siblingKeys}
          onChange={(key) => onChange({ ...value, key })}
        />
        <div className='d-flex align-items-center gap-3'>
          {!!unsaved && <span className='chip chip--xs'>Not saved</span>}
          {!!onRemove && !readOnly && (
            <Button
              theme='text'
              onClick={onRemove}
              id='delete-multivariate'
              aria-label='Remove variant'
            >
              <Icon name='trash-2' width={20} fill={colorIconSecondary} />
            </Button>
          )}
        </div>
      </Row>
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
                value={Utils.getTypedValue(Utils.featureStateToValue(value))}
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
      <Row className='justify-content-between align-items-center mt-2'>
        <label className='mb-0'>{weightTitle}</label>
        <div className='d-flex align-items-center gap-2'>
          <div className='variant-card__weight'>
            <Input
              type='number'
              size='small'
              underline
              centered
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
              value={value.default_percentage_allocation ?? ''}
              readOnly={disabled}
              step='any'
            />
          </div>
          <span className='text-muted'>%</span>
        </div>
      </Row>
      {!!apiError && (
        <div className='mt-2'>
          <ErrorMessage error={apiError} />
        </div>
      )}
    </div>
  )
}
