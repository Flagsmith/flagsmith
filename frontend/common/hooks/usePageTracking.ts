import { useEffect } from 'react'

/**
 * Options for configuring page tracking behavior.
 */
export type PageTrackingOptions = {
  /** The page constant name from Constants.pages */
  pageName: string
  /** Context data for tracking and storage persistence */
  context?: {
    environmentId?: string
    projectId?: number
    organisationId?: number
  }
  /** Whether to save context to AsyncStorage (default: false) */
  saveToStorage?: boolean
  /** Custom dependencies for re-tracking on changes */
  deps?: React.DependencyList
}

/**
 * Unified hook for tracking page views with optional context persistence.
 *
 * Consolidates both page tracking and environment context storage into a single,
 * flexible hook. Automatically calls API.trackPage and optionally persists
 * environment context to AsyncStorage.
 *
 * @param options - Configuration object for page tracking
 *
 * @example
 * ```tsx
 * // Basic page tracking only
 * usePageTracking({ pageName: Constants.pages.FEATURES })
 *
 * // With context and storage persistence
 * usePageTracking({
 *   pageName: Constants.pages.FEATURES,
 *   context: { environmentId, projectId, organisationId },
 *   saveToStorage: true,
 * })
 *
 * // With custom dependencies
 * usePageTracking({
 *   pageName: Constants.pages.FEATURES,
 *   context: { projectId },
 *   deps: [projectId, someOtherDep],
 * })
 * ```
 */
export function usePageTracking(options: PageTrackingOptions): void {
  const { context, deps = [], pageName, saveToStorage = false } = options

  // Track page view
  useEffect(() => {
    if (typeof API !== 'undefined' && API.trackPage) {
      API.trackPage(pageName)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  // Persist environment context to storage if enabled
  useEffect(() => {
    if (saveToStorage && context) {
      if (typeof AsyncStorage !== 'undefined' && AsyncStorage.setItem) {
        AsyncStorage.setItem(
          'lastEnv',
          JSON.stringify({
            environmentId: context.environmentId,
            orgId: context.organisationId,
            projectId: context.projectId,
          }),
        )
      }
    }
    // We intentionally use individual properties instead of context object
    // to prevent re-runs when object reference changes but values don't
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    saveToStorage,
    context?.environmentId,
    context?.organisationId,
    context?.projectId,
  ])
}
