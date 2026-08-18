import { FeatureState } from 'common/types/responses'

const normaliseMultivariate = (featureState?: FeatureState) => {
  const values = featureState?.multivariate_feature_state_values || []
  return values
    .map((v) => ({
      multivariate_feature_option: Number(v?.multivariate_feature_option) || 0,
      percentage_allocation: Number(v?.percentage_allocation) || 0,
    }))
    .sort((a, b) => {
      if (a.multivariate_feature_option !== b.multivariate_feature_option) {
        return a.multivariate_feature_option - b.multivariate_feature_option
      }
      return a.percentage_allocation - b.percentage_allocation
    })
}

export const hasMultivariateChange = (
  leftFeatureState?: FeatureState,
  rightFeatureState?: FeatureState,
) => {
  const left = normaliseMultivariate(leftFeatureState)
  const right = normaliseMultivariate(rightFeatureState)

  if (left.length !== right.length) {
    return true
  }

  for (let i = 0; i < left.length; i++) {
    if (
      left[i].multivariate_feature_option !==
        right[i].multivariate_feature_option ||
      left[i].percentage_allocation !== right[i].percentage_allocation
    ) {
      return true
    }
  }

  return false
}
