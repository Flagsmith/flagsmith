import {
  FeatureConflict,
  FeatureState,
  FeatureStateWithConflict,
  Segment,
  SegmentCondition,
  SegmentRule,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import { sortBy, uniqBy } from 'lodash'

export function getFeatureStateDiff(
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureStateWithConflict | undefined,
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
    conflict: newFeatureState?.conflict,
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

export type TDiffSegmentOverride = {
  segment: Segment
  newEnabled: boolean
  newPriority: number
  newValue: string
  oldEnabled: boolean
  oldPriority: number
  oldValue: string
  conflict?: FeatureConflict
  totalChanges: number
  variationDiff?: {
    diffs: TDiffVariation[]
    totalChanges: number
  }
  created: boolean
  deleted: boolean
}
export type TDiffVariation = {
  hasChanged: boolean
  variationOption: number
  newWeight: number
  oldWeight: number
}
export type TDiffVariations = {
  diffs: TDiffVariation[]
  totalChanges: number
}

export const getSegmentOverrideDiff = (
  oldFeatureStates: FeatureStateWithConflict[] | undefined,
  newFeatureStates: FeatureStateWithConflict[] | undefined,
  segments: Segment[] | undefined,
  conflicts?: FeatureConflict[] | undefined,
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
  let totalConflicts = 0
  const diffs = relatedSegments?.map((segment) => {
    const oldFeatureState = oldFeatureStates?.find(
      (v) => v.feature_segment?.segment === segment.id,
    )
    const newFeatureState = newFeatureStates?.find(
      (v) => v.feature_segment?.segment === segment.id,
    )
    let foundConflict = null
    if (!newFeatureState && !!oldFeatureState) {
      //detect conflicts where the new change request attempts to delete a segment overrides
      foundConflict = conflicts?.find(
        (v) => v.segment_id === oldFeatureState.feature_segment?.segment,
      )
      if (foundConflict) {
        totalConflicts++
      }
    }

    const variationDiff = getVariationDiff(oldFeatureState, newFeatureState)

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
    if (newFeatureState?.conflict) {
      totalConflicts++
    }
    const segmentChanges =
      (enabledChanged ? 1 : 0) +
      (valueChanged ? 1 : 0) +
      variationDiff.totalChanges +
      (priorityChanged ? 1 : 0)
    if (segmentChanges) {
      totalChanges += 1
    }
    return {
      conflict: foundConflict || newFeatureState?.conflict,
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
      variationDiff,
    } as TDiffSegmentOverride
  })
  return {
    diffs,
    totalChanges,
    totalConflicts,
  }
}

export const getVariationDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
) => {
  let totalChanges = 0
  const variationOptions = uniqBy(
    oldFeatureState?.multivariate_feature_state_values ||
      [].concat(newFeatureState?.multivariate_feature_state_values || []),
    (v) => v.multivariate_feature_option,
  )
  const diffs = variationOptions.map((variationOption) => {
    const oldMV = oldFeatureState?.multivariate_feature_state_values?.find(
      (v) =>
        v.multivariate_feature_option ===
        variationOption.multivariate_feature_option,
    )
    const newMV = newFeatureState?.multivariate_feature_state_values?.find(
      (v) =>
        v.multivariate_feature_option ===
        variationOption.multivariate_feature_option,
    )

    const oldWeight = oldMV?.percentage_allocation
    const newWeight = newMV?.percentage_allocation
    const hasChanged = oldWeight !== newWeight
    if (hasChanged) {
      totalChanges += 1
    }
    return {
      hasChanged,
      newWeight,
      oldWeight,
      variationOption: variationOption.multivariate_feature_option,
    } as TDiffVariation
  })

  return {
    diffs,
    totalChanges,
  } as TDiffVariations
}

export type TSegmentDiff = {
  newString: string
  oldString: string
  totalChanges: number
}

export function getSegmentDiff(
  oldSegment: Segment | undefined,
  newSegment: Segment | undefined,
): TSegmentDiff {
  const oldRules = oldSegment?.rules || []
  const newRules = newSegment?.rules || []
  const oldString = getRulesDiff(oldRules, 0)
  const newString = getRulesDiff(newRules, 0)
  return { newString, oldString, totalChanges: newString === oldString ? 0 : 1 }
}

function getRulesDiff(
  rules: SegmentRule[],
  level: number,
  currentString = '',
): string {
  const indent = '  '.repeat(level)
  let str = currentString || `${indent}\n`

  rules.forEach((rule, i) => {
    const prepend = i > 0 ? 'And ' : ''

    if (rule.type === 'ANY') {
      str += `${indent}------ ${prepend}Any of the following ------\n`
    } else if (rule.type === 'NONE') {
      str += `${indent}------  ${prepend}None of the following ------\n`
    }
    str = getConditionsDiff(rule.conditions, level + 1, str)
    if (rule.rules) {
      str = getRulesDiff(rule.rules, level + 1, str)
    }
  })

  return str
}

function getConditionsDiff(
  conditions: SegmentCondition[],
  level: number,
  currentString: string,
): string {
  const operators = Utils.getFlagsmithJSONValue('segment_operators', [])
  const indent = '  '.repeat(level)
  let str = currentString

  conditions.forEach((condition, index) => {
    const operatorLabel = operators.find(
      (o) => o.value === condition.operator,
    )?.label
    const line = [condition.property, operatorLabel, condition.value]
      .filter(Boolean)
      .join(' ')

    str += `${indent}${line}\n`
  })

  return str
}
