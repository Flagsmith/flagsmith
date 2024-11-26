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

export type TSegmentRuleDiff = {
  oldRule?: SegmentRule
  newRule?: SegmentRule
  hasChanged: boolean
  conditions: {
    old: SegmentCondition | undefined
    new: SegmentCondition | undefined
    hasChanged: boolean
  }[]
  rules?: TSegmentRuleDiff[]
}

export type TSegmentDiff = {
  totalChanges: number
  changes: TSegmentRuleDiff[]
}

export function getSegmentDiff(
  oldSegment: Segment | undefined,
  newSegment: Segment | undefined,
): TSegmentDiff {
  const oldRules = oldSegment?.rules || []
  const newRules = newSegment?.rules || []

  const { changes, totalChanges } = getRulesDiff(oldRules, newRules)

  return { changes, totalChanges }
}

function getRulesDiff(
  oldRules: SegmentRule[],
  newRules: SegmentRule[],
): {
  totalChanges: number
  changes: TSegmentRuleDiff[]
} {
  const ruleChanges: TSegmentRuleDiff[] = []
  let totalChanges = 0

  const matchedIds = new Set<number | undefined>()

  // Compare rules based on IDs
  newRules.forEach((newRule) => {
    const oldRule = oldRules.find((rule) => rule.id === newRule.id)
    matchedIds.add(newRule.id)

    const conditionDiff = getConditionsDiff(
      oldRule?.conditions || [],
      newRule.conditions || [],
    )

    if (oldRule) {
      // Recursively diff nested rules
      const subDiff = getRulesDiff(oldRule.rules || [], newRule.rules || [])

      const hasChanged =
        JSON.stringify({
          ...oldRule,
          conditions: undefined,
          rules: undefined,
        }) !==
          JSON.stringify({
            ...newRule,
            conditions: undefined,
            rules: undefined,
          }) ||
        conditionDiff.totalChanges > 0 ||
        subDiff.totalChanges > 0

      if (hasChanged) {
        totalChanges++
      }

      ruleChanges.push({
        conditions: sortBy(
          conditionDiff.conditions,
          (v) => (v.new || v.old)?.id,
        ),
        hasChanged,
        newRule,
        oldRule,
        rules: subDiff.changes,
      })

      totalChanges += conditionDiff.totalChanges + subDiff.totalChanges
    } else {
      // New rule added
      totalChanges += conditionDiff.totalChanges
      ruleChanges.push({
        conditions: sortBy(
          conditionDiff.conditions,
          (v) => (v.new || v.old)?.id,
        ),
        hasChanged: true,
        newRule,
        oldRule: undefined,
      })
    }
  })

  // Handle removed rules in `oldRules`
  oldRules.forEach((oldRule) => {
    if (!matchedIds.has(oldRule.id)) {
      const conditionDiff = getConditionsDiff(oldRule.conditions || [], [])

      totalChanges += conditionDiff.totalChanges
      ruleChanges.push({
        conditions: conditionDiff.conditions,
        hasChanged: true,
        newRule: undefined,
        oldRule,
      })
    }
  })

  return { changes: ruleChanges, totalChanges }
}

function getConditionsDiff(
  oldConditions: SegmentCondition[],
  newConditions: SegmentCondition[],
): {
  totalChanges: number
  conditions: TSegmentRuleDiff['conditions']
} {
  const conditions: TSegmentRuleDiff['conditions'] = []
  const processedIds = new Set<number | undefined>()
  let totalChanges = 0

  // Match conditions by `id`
  newConditions.forEach((newCondition) => {
    const oldCondition = oldConditions.find(
      (cond) => cond.id === newCondition.id,
    )
    processedIds.add(newCondition.id)

    const hasChanged =
      !oldCondition ||
      JSON.stringify({ ...oldCondition, id: undefined }) !==
        JSON.stringify({ ...newCondition, id: undefined })

    conditions.push({
      hasChanged,
      new: newCondition,
      old: oldCondition,
    })

    if (hasChanged) totalChanges++
  })

  // Handle removed conditions in `oldConditions`
  oldConditions.forEach((oldCondition) => {
    if (!processedIds.has(oldCondition.id)) {
      conditions.push({
        hasChanged: true,
        new: undefined,
        old: oldCondition,
      })
      totalChanges++
    }
  })

  return { conditions, totalChanges }
}
