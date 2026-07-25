import type { FeatureState } from 'common/types/responses'

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
  return (
    results?.find((featureState) => featureState.feature === featureId) ??
    results?.[0]
  )
}
