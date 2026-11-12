import { FeatureState } from 'common/types/responses'
import { hasMultivariateChange } from 'common/utils/compareMultivariate'

const featureState = (
  multivariate_feature_state_values: FeatureState['multivariate_feature_state_values'],
): FeatureState =>
  ({
    multivariate_feature_state_values,
  } as FeatureState)

describe('hasMultivariateChange', () => {
  it('returns false when both sides have no multivariate values', () => {
    expect(hasMultivariateChange(featureState([]), featureState([]))).toBe(
      false,
    )
    expect(hasMultivariateChange(undefined, undefined)).toBe(false)
  })

  it('returns true when percentage allocations differ', () => {
    const left = featureState([
      { id: 1, multivariate_feature_option: 10, percentage_allocation: 0 },
    ])
    const right = featureState([
      { id: 2, multivariate_feature_option: 10, percentage_allocation: 100 },
    ])

    expect(hasMultivariateChange(left, right)).toBe(true)
  })

  it('returns true when the number of multivariate options differs', () => {
    const left = featureState([
      { id: 1, multivariate_feature_option: 10, percentage_allocation: 50 },
    ])
    const right = featureState([
      { id: 2, multivariate_feature_option: 10, percentage_allocation: 50 },
      { id: 3, multivariate_feature_option: 11, percentage_allocation: 50 },
    ])

    expect(hasMultivariateChange(left, right)).toBe(true)
  })

  it('returns false when values match regardless of array order', () => {
    const left = featureState([
      { id: 1, multivariate_feature_option: 10, percentage_allocation: 0 },
      { id: 2, multivariate_feature_option: 11, percentage_allocation: 100 },
    ])
    const right = featureState([
      { id: 3, multivariate_feature_option: 11, percentage_allocation: 100 },
      { id: 4, multivariate_feature_option: 10, percentage_allocation: 0 },
    ])

    expect(hasMultivariateChange(left, right)).toBe(false)
  })
})
