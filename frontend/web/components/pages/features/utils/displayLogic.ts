/**
 * Pure utility functions for display logic on the Features page.
 */

import type { FilterState } from 'components/pages/features/components/FeaturesTableFilters'

/**
 * Determines if the initial loading state should be shown.
 * Shows loader only on first load when data hasn't been loaded yet and no flags exist.
 */
export function shouldShowInitialLoader(
  isLoading: boolean,
  loadedOnce: boolean,
  projectFlags: unknown[] | undefined,
): boolean {
  return (isLoading || !loadedOnce) && (!projectFlags || !projectFlags.length)
}

/**
 * Determines if the main content (features list) should be shown.
 * Shows content if loaded at least once OR if filters are active.
 */
export function shouldShowContent(
  loadedOnce: boolean,
  filters: FilterState,
  isLoading: boolean,
): boolean {
  return (
    loadedOnce ||
    ((filters.showArchived ||
      typeof filters.search === 'string' ||
      !!filters.tags.length) &&
      !isLoading)
  )
}

/**
 * Determines if the empty state should be shown.
 * Shows empty state when not loading, has loaded once, but has no content to show.
 */
export function shouldShowEmptyState(
  isLoading: boolean,
  loadedOnce: boolean,
  showContent: boolean,
): boolean {
  return !isLoading && loadedOnce && !showContent
}
