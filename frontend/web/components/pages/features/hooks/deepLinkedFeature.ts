import type {
  FeatureState,
  FeatureStateValue,
  FlagsmithValue,
} from 'common/types/responses'

type FlattenableFeatureStateValue = FlagsmithValue | FeatureStateValue

// The featurestates endpoint returns a nested value; the list path is flat.
// Mirrors Utils.featureStateToValue, inlined to keep the Flux stores out.
function flattenFeatureStateValue(
  value: FlattenableFeatureStateValue | undefined,
): FlagsmithValue {
  if (value === null || value === undefined) {
    return null
  }
  if (typeof value !== 'object') {
    return value
  }
  switch (value.type) {
    case 'bool':
      return value.boolean_value
    case 'float':
      return value.float_value ?? null
    case 'int':
      return value.integer_value ?? null
    default:
      return value.string_value
  }
}

/**
 * Decides whether the `?feature=` deep link targets a feature that is NOT on the
 * currently loaded page, and therefore needs to be fetched directly.
 *
 * Returns `null` (no direct fetch needed) when there is no param, the list has
 * not loaded yet, the param is not a valid id, or the feature is already on the
 * current page (in which case its rendered row handles the deep link).
 */
export function shouldDeepFetchFeature(args: {
  featureParam: string | undefined
  projectFlags: { id: number }[]
  isListLoaded: boolean
}): { featureId: number } | null {
  const { featureParam, isListLoaded, projectFlags } = args
  if (!isListLoaded || !featureParam) {
    return null
  }
  const featureId = Number(featureParam)
  if (!Number.isInteger(featureId)) {
    return null
  }
  const isOnPage = projectFlags.some((flag) => flag.id === featureId)
  return isOnPage ? null : { featureId }
}

/** Pick the environment feature state matching `featureId`, falling back to the
 * first result, or `undefined` when there is none. */
export function pickEnvironmentFlag(
  results: FeatureState[] | undefined,
  featureId: number,
): FeatureState | undefined {
  const match =
    results?.find((featureState) => featureState.feature === featureId) ??
    results?.[0]
  if (!match) {
    return undefined
  }
  return {
    ...match,
    feature_state_value: flattenFeatureStateValue(match.feature_state_value),
  }
}
