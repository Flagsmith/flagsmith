import React, { FC, ReactNode } from 'react'
import ValueEditor from 'components/ValueEditor'
import ErrorMessage from 'components/ErrorMessage'
import { VariationValueInput } from './VariationValueInput'
import Utils from 'common/utils/utils'
import { FlagsmithValue, MultivariateOption } from 'common/types/responses'
import { UnmatchedOverride } from 'common/utils/multivariate'
import { VariantKey } from './VariantKey'

type VariationOverride = {
  id?: number
  multivariate_feature_option: number
  percentage_allocation: number
  multivariate_feature_option_index?: number
}

interface VariationOptionsProps {
  apiErrors?: (string | null)[]
  canCreateFeature: boolean
  controlPercentage: number
  controlValue: FlagsmithValue
  disabled: boolean
  multivariateOptions: MultivariateOption[]
  readOnly?: boolean
  removeVariation: (i: number) => void
  select?: boolean
  // An override value that is neither the control value nor one of the
  // variations. Shown read-only, so the identity does not read as being on the
  // control value. Stays listed once deselected — it is only gone on save.
  unmatchedOverride?: UnmatchedOverride
  setValue: (value: FlagsmithValue) => void
  setVariations: (variations: VariationOverride[]) => void
  unsavedVariations?: boolean[]
  updateVariation: (
    index: number,
    value: MultivariateOption,
    variationOverrides: VariationOverride[],
  ) => void
  variationOverrides: VariationOverride[]
  weightTitle: string
}

interface ValueRowLabelProps {
  children: ReactNode
}

// Each row shows a bare value, so it needs saying which value it is.
const ValueRowLabel: FC<ValueRowLabelProps> = ({ children }) => (
  <div className='mb-2'>
    <span className='h6 mb-0 font-weight-semibold'>{children}</span>
  </div>
)

export const VariationOptions: FC<VariationOptionsProps> = ({
  apiErrors,
  canCreateFeature,
  controlPercentage,
  controlValue,
  disabled,
  multivariateOptions,
  readOnly,
  removeVariation,
  select,
  setValue,
  setVariations,
  unmatchedOverride,
  unsavedVariations,
  updateVariation,
  variationOverrides,
  weightTitle,
}) => {
  const invalid = multivariateOptions.length && controlPercentage < 0
  if (!multivariateOptions || !multivariateOptions.length) {
    return null
  }
  const controlSelected =
    !unmatchedOverride?.selected &&
    (!variationOverrides ||
      !variationOverrides.find((v) => v.percentage_allocation === 100))
  return (
    <>
      {invalid && (
        <ErrorMessage
          className='mt-2'
          error='Your variation percentage splits total to over 100%'
        />
      )}
      {select && !!unmatchedOverride && (
        <div className='panel panel--flat panel-without-heading mb-2'>
          <div className='panel-content'>
            <ValueRowLabel>Current override</ValueRowLabel>
            <Row>
              <Flex>
                <ValueEditor
                  disabled
                  value={Utils.getTypedValue(unmatchedOverride.value)}
                />
              </Flex>
              <div
                data-test='select-unmatched-override'
                onMouseDown={(e) => {
                  e.stopPropagation()
                  setVariations([])
                  setValue?.(unmatchedOverride.value)
                }}
                className={`btn-radio ml-2 ${
                  unmatchedOverride.selected ? 'btn-radio-on' : ''
                }`}
              />
            </Row>
          </div>
        </div>
      )}
      {select && (
        <div className='panel panel--flat panel-without-heading mb-2'>
          <div className='panel-content'>
            <ValueRowLabel>Control value</ValueRowLabel>
            <Row>
              <Flex>
                <ValueEditor
                  disabled
                  value={Utils.getTypedValue(controlValue)}
                />
              </Flex>
              <div
                onMouseDown={(e) => {
                  e.stopPropagation()
                  setVariations([])
                  setValue?.(controlValue)
                }}
                className={`btn-radio ml-2 ${
                  controlSelected ? 'btn-radio-on' : ''
                }`}
              />
            </Row>
          </div>
        </div>
      )}
      {multivariateOptions.map((theValue, i) => {
        let override: (typeof variationOverrides)[number] | false | undefined
        if (select) {
          const hasIndex =
            variationOverrides?.[0] &&
            typeof variationOverrides[0].multivariate_feature_option_index ===
              'number'
          if (hasIndex) {
            override =
              i === variationOverrides[0].multivariate_feature_option_index &&
              variationOverrides[0]
          } else {
            override = variationOverrides?.find(
              (v) => v.multivariate_feature_option === theValue.id,
            )
          }
        } else {
          override = variationOverrides?.find(
            (v) => v.percentage_allocation === 100,
          )
        }
        return select ? (
          <div key={i} className='panel panel--flat panel-without-heading mb-2'>
            <div className='panel-content'>
              <ValueRowLabel>
                <VariantKey value={theValue.key} index={i} />
              </ValueRowLabel>
              <Row>
                <Flex>
                  <ValueEditor
                    disabled={true}
                    value={Utils.getTypedValue(
                      Utils.featureStateToValue(theValue),
                    )}
                  />
                </Flex>
                <div
                  data-test={`select-variation-${Utils.featureStateToValue(
                    theValue,
                  )}`}
                  onMouseDown={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    setVariations([
                      {
                        multivariate_feature_option: theValue.id,
                        multivariate_feature_option_index: i,
                        percentage_allocation: 100,
                      },
                    ])
                    return false
                  }}
                  className={`btn-radio ml-2 ${override ? 'btn-radio-on' : ''}`}
                />
              </Row>
            </div>
          </div>
        ) : (
          <VariationValueInput
            key={i}
            index={i}
            apiError={apiErrors?.[i]}
            canCreateFeature={canCreateFeature}
            readOnly={readOnly ?? false}
            unsaved={unsavedVariations?.[i]}
            value={theValue}
            // Effective keys: unset labels persist as their Variant_n
            // fallback, so they count for uniqueness too.
            siblingKeys={multivariateOptions
              .map(
                (option, index) =>
                  option.key || Utils.getDefaultVariantKey(index),
              )
              .filter((_, index) => index !== i)}
            onChange={(e) => {
              updateVariation(i, e, variationOverrides)
            }}
            weightTitle={weightTitle}
            disabled={disabled}
            onRemove={
              readOnly || disabled ? undefined : () => removeVariation(i)
            }
          />
        )
      })}
    </>
  )
}
