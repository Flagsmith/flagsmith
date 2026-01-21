import React from 'react'
import ValueEditor from 'components/ValueEditor'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'
import { VariationValueInput } from './VariationValueInput'
import Utils from 'common/utils/utils'
interface VariationOptionsProps {
  canCreateFeature: boolean
  controlPercentage: number
  controlValue: any
  disabled: boolean
  multivariateOptions: any[]
  readOnly?: boolean
  removeVariation: (i: number) => void
  select?: boolean
  setValue: (value: any) => void
  setVariations: (variations: any[]) => void
  updateVariation: (
    index: number,
    value: any,
    variationOverrides: any[],
  ) => void
  variationOverrides: any[]
  weightTitle: string
}

export const VariationOptions: React.FC<VariationOptionsProps> = ({
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
  updateVariation,
  variationOverrides,
  weightTitle,
}) => {
  const invalid = multivariateOptions.length && controlPercentage < 0
  if (!multivariateOptions || !multivariateOptions.length) {
    return null
  }
  const controlSelected =
    !variationOverrides ||
    !variationOverrides.find((v) => v.percentage_allocation === 100)
  return (
    <>
      {invalid && (
        <ErrorMessage
          className='mt-2'
          error='Your variation percentage splits total to over 100%'
        />
      )}
      {!readOnly && (
        <p className='mb-4'>
          <InfoMessage collapseId={'variation-value'}>
            Changing a Variation Value will affect{' '}
            <strong>all environments</strong>, their weights are specific to
            this environment. Existing users will see the new variation value if
            it is changed. These values will only apply when you identify via
            the SDK.
            <a
              target='_blank'
              href='https://docs.flagsmith.com/basic-features/managing-features#multi-variate-flags'
              rel='noreferrer'
            >
              Check the Docs for more details
            </a>
            .
          </InfoMessage>
        </p>
      )}

      {select && (
        <div className='panel panel--flat panel-without-heading mb-2'>
          <div className='panel-content'>
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
          <div className='panel panel--flat panel-without-heading mb-2'>
            <div className='panel-content'>
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
            canCreateFeature={canCreateFeature}
            readOnly={readOnly ?? false}
            value={theValue}
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
