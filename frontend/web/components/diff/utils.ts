import { FeatureState } from 'common/types/responses'
import Utils from 'common/utils/utils'
export function getFeatureStateDiff(
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
) {
  const oldValue = `${Utils.getTypedValue(
    Utils.featureStateToValue(oldFeatureState?.feature_state_value),
  )}`
  const newValue = `${Utils.getTypedValue(
    Utils.featureStateToValue(newFeatureState?.feature_state_value),
  )}`
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

export const getSegmentDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
  segmentName: string,
) => {
  const oldName = oldFeatureState ? segmentName : ''
  const oldEnabled = oldFeatureState ? `${!!oldFeatureState?.enabled}` : ''
  const oldPriority = oldFeatureState?.feature_segment
    ? `${oldFeatureState.feature_segment.priority + 1}`
    : ''
  const newPriority = newFeatureState?.feature_segment
    ? `${newFeatureState.feature_segment.priority + 1}`
    : ''
  const newEnabled = newFeatureState ? `${!!newFeatureState?.enabled}` : ''

  const oldValue = `${Utils.getTypedValue(
    oldFeatureState
      ? Utils.featureStateToValue(oldFeatureState?.feature_state_value)
      : '',
  )}`
  const newValue = `${Utils.getTypedValue(
    newFeatureState
      ? Utils.featureStateToValue(newFeatureState?.feature_state_value)
      : '',
  )}`

  const newName = newFeatureState ? segmentName : ''
  const enabledChanged = oldEnabled !== newEnabled
  const valueChanged = oldValue !== newValue
  const priorityChanged = oldPriority !== newPriority
  return {
    enabledChanged,
    newEnabled,
    newName,
    newPriority,
    newValue,
    oldEnabled,
    oldName,
    oldPriority,
    oldValue,
    totalChanges:
      (enabledChanged ? 1 : 0) +
      (valueChanged ? 1 : 0) +
      (priorityChanged ? 1 : 0),
  }
}
