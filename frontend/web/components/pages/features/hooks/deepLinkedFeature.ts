import Utils from 'common/utils/utils'
import type { FeatureState, FeatureStateValue } from 'common/types/responses'

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
 * first result, or `undefined` when there is none.
 *
 * `features/featurestates/` serialises `feature_state_value` as a nested
 * `{type, string_value, ...}` object, whereas the paginated feature list
 * flattens it to a scalar. Normalise to the scalar here so the slideout gets
 * the same shape whichever path opened it — otherwise the value editor
 * stringifies the object and renders `[object Object]`.
 *
 * ponytail: normalising at this boundary mirrors ConnectedFeatureOverrideRow.
 * The deeper fix is typing this endpoint's response separately from
 * `FeatureState` so the mismatch can't go unnoticed again.
 */
export function pickEnvironmentFlag(
  results: FeatureState[] | undefined,
  featureId: number,
): FeatureState | undefined {
  const featureState =
    results?.find((featureState) => featureState.feature === featureId) ??
    results?.[0]
  if (!featureState) {
    return featureState
  }
  return {
    ...featureState,
    // `?? null` because featureStateToValue returns undefined for an
    // unrecognised shape, and FlagsmithValue has no undefined.
    feature_state_value:
      Utils.featureStateToValue(
        featureState.feature_state_value as unknown as FeatureStateValue,
      ) ?? null,
  }
}
