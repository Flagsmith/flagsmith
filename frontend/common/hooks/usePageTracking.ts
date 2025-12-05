import { useEffect } from 'react'

/**
 * Generic hook for tracking page views with analytics.
 *
 * Internal helper used by usePageTrackingWithContext.
 * Automatically calls API.trackPage when the component mounts or dependencies change.
 *
 * @param pageName - The page constant name from Constants.pages
 * @param deps - Optional dependency array for re-tracking on changes (defaults to empty array for mount-only)
 */
function usePageTracking(
  pageName: string,
  deps: React.DependencyList = [],
): void {
  useEffect(() => {
    if (typeof API !== 'undefined' && API.trackPage) {
      API.trackPage(pageName)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}

/**
 * Extended page tracking hook that also persists environment context to storage.
 *
 * Used by pages that need to remember the last selected environment/project
 * for restoration on next visit. Internally uses usePageTracking for analytics.
 *
 * @param pageName - The page constant name from Constants.pages
 * @param environmentId - The current environment ID (API key)
 * @param projectId - The current project ID
 * @param organisationId - The current organisation ID
 *
 * @example
 * ```tsx
 * usePageTrackingWithContext(
 *   Constants.pages.FEATURES,
 *   environmentApiKey,
 *   projectId,
 *   organisationId
 * )
 * ```
 */
export function usePageTrackingWithContext(
  pageName: string,
  environmentId: string,
  projectId: number,
  organisationId?: number,
): void {
  // Track page view using base hook
  usePageTracking(pageName, [environmentId, projectId, organisationId])

  // Persist environment context to storage
  useEffect(() => {
    if (typeof AsyncStorage !== 'undefined' && AsyncStorage.setItem) {
      AsyncStorage.setItem(
        'lastEnv',
        JSON.stringify({
          environmentId,
          orgId: organisationId,
          projectId,
        }),
      )
    }
  }, [environmentId, projectId, organisationId])
}
