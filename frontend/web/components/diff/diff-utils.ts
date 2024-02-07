import { FeatureState, ProjectFlag, Segment } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { sortBy } from 'lodash'
export function getFeatureStateDiff(
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
) {
  const oldValue = Utils.getTypedValue(
    Utils.featureStateToValue(oldFeatureState?.feature_state_value),
  )
  const newValue = Utils.getTypedValue(
    Utils.featureStateToValue(newFeatureState?.feature_state_value),
  )
  const oldEnabled = !!oldFeatureState?.enabled
  const newEnabled = !!newFeatureState?.enabled
  const enabledChanged = oldEnabled !== newEnabled
  const valueChanged = oldValue !== newValue
  const diff = {
    enabledChanged,
    newEnabled,
    newValue,
    oldEnabled,
    oldValue,
    totalChanges: (enabledChanged ? 1 : 0) + (valueChanged ? 1 : 0),
    valueChanged,
  }
  return diff
}

export type TDiffSegment = {
  segment: Segment
  newEnabled: boolean
  newPriority: number
  newValue: string
  oldEnabled: boolean
  oldPriority: number
  oldValue: string
  totalChanges: number
  created: boolean
  deleted: boolean
}
export type TDiffVariation = {
  hasChanged: boolean
  newValue: string
  newWeight: number
  oldValue: string
  oldWeight: number
}
export type TDiffVariations = {
  diffs: TDiffVariation[]
  totalChanges: number
}

export const getSegmentDiff = (
  oldFeatureStates: FeatureState[] | undefined,
  newFeatureStates: FeatureState[] | undefined,
  segments: Segment[] | undefined,
) => {
  if (!oldFeatureStates || !newFeatureStates || !segments) {
    return null
  }

  const relatedSegments = sortBy(
    segments?.filter((segment) => {
      return newFeatureStates
        .concat(oldFeatureStates)
        .find((v) => v.feature_segment?.segment === segment.id)
    }),
    (s) => s.name,
  )
  let totalChanges = 0
  const diffs = relatedSegments?.map((segment) => {
    const oldFeatureState = oldFeatureStates?.find(
      (v) => v.feature_segment?.segment === segment.id,
    )
    const newFeatureState = newFeatureStates?.find(
      (v) => v.feature_segment?.segment === segment.id,
    )

    const oldEnabled = !!oldFeatureState?.enabled
    const oldPriority = oldFeatureState?.feature_segment
      ? oldFeatureState.feature_segment.priority + 1
      : -1
    const newPriority = newFeatureState?.feature_segment
      ? newFeatureState.feature_segment.priority + 1
      : -1
    const newEnabled = !!newFeatureState?.enabled

    const oldValue = Utils.getTypedValue(
      oldFeatureState
        ? Utils.featureStateToValue(oldFeatureState?.feature_state_value)
        : '',
    )
    const newValue = Utils.getTypedValue(
      newFeatureState
        ? Utils.featureStateToValue(newFeatureState?.feature_state_value)
        : '',
    )

    const enabledChanged = oldEnabled !== newEnabled
    const valueChanged = oldValue !== newValue
    const priorityChanged = oldPriority !== newPriority
    const segmentChanges =
      (enabledChanged ? 1 : 0) +
      (valueChanged ? 1 : 0) +
      (priorityChanged ? 1 : 0)
    if (segmentChanges) {
      totalChanges += 1
    }
    return {
      created: !oldFeatureState,
      deleted: !newFeatureState,
      enabledChanged,
      newEnabled,
      newPriority,
      newValue,
      oldEnabled,
      oldPriority,
      oldValue,
      segment,
      totalChanges: segmentChanges,
    } as TDiffSegment
  })
  return {
    diffs,
    totalChanges,
  }
}

export const getVariationDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
  feature: ProjectFlag | undefined,
) => {
  let totalChanges = 0
  const diffs = feature?.multivariate_options?.map((variationOption) => {
    const oldMV = oldFeatureState?.multivariate_feature_state_values?.find(
      (v) => v.multivariate_feature_option === variationOption.id,
    )
    const newMV = newFeatureState?.multivariate_feature_state_values?.find(
      (v) => v.multivariate_feature_option === variationOption.id,
    )

    const oldValue = variationOption.string_value
    const newValue = variationOption.string_value // todo: This would eventually be based on the old and new feature versions
    const oldWeight = oldMV?.percentage_allocation
    const newWeight = newMV?.percentage_allocation
    const hasChanged = oldWeight !== newWeight || oldValue !== newValue
    if (hasChanged) {
      totalChanges += 1
    }
    return {
      hasChanged,
      newValue,
      newWeight,
      oldValue,
      oldWeight,
    } as TDiffVariation
  })

  return {
    diffs,
    totalChanges,
  } as TDiffVariations
}
