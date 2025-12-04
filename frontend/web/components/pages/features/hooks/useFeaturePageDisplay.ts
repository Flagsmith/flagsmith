import { useState, useEffect, useMemo } from 'react'
import type { ProjectFlag } from 'common/types/responses'
import type { FilterState } from 'components/pages/features/components/FeaturesTableFilters'

// ============================================================================
// Internal Helper Functions
// ============================================================================

/**
 * Determines if the initial loading state should be shown.
 * Shows loader only on first load when data hasn't been loaded yet and no flags exist.
 */
function shouldShowInitialLoader(
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
function shouldShowContent(
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
function shouldShowEmptyState(
  isLoading: boolean,
  loadedOnce: boolean,
  showContent: boolean,
): boolean {
  return !isLoading && loadedOnce && !showContent
}

/**
 * Determines if the "Create Feature" button should be shown.
 * Shows button when features have loaded at least once OR when filters are active.
 */
function shouldShowCreateButton(
  loadedOnce: boolean,
  filters: FilterState,
): boolean {
  return loadedOnce || filters.showArchived || !!filters.tags?.length
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for managing feature page display state (loaders, content, empty states).
 *
 * Consolidates all display logic into a single hook, including the `loadedOnce`
 * state management and display flag computations.
 *
 * @param isLoading - Whether the query is currently loading
 * @param projectFlags - The current list of project flags
 * @param filters - The current filter state
 * @param data - The raw data from the query (used to track first load)
 * @returns Object containing showInitialLoader, showContent, showEmptyState, and loadedOnce flags
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useGetFeatureListQuery(params)
 * const { projectFlags } = useFeaturePageData(data)
 * const { showInitialLoader, showContent, showEmptyState } = useFeaturePageDisplay(
 *   isLoading,
 *   projectFlags,
 *   filters,
 *   data
 * )
 *
 * return (
 *   <>
 *     {showInitialLoader && <Loader />}
 *     {showContent && <FeaturesList />}
 *     {showEmptyState && <EmptyState />}
 *   </>
 * )
 * ```
 */
export function useFeaturePageDisplay(
  isLoading: boolean,
  projectFlags: ProjectFlag[],
  filters: FilterState,
  data: unknown,
): {
  showInitialLoader: boolean
  showContent: boolean
  showEmptyState: boolean
  shouldShowCreateButton: boolean
  loadedOnce: boolean
} {
  const [loadedOnce, setLoadedOnce] = useState(false)

  useEffect(() => {
    if (data && !loadedOnce) {
      setLoadedOnce(true)
    }
  }, [data, loadedOnce])

  const displayFlags = useMemo(() => {
    const showInitLoader = shouldShowInitialLoader(
      isLoading,
      loadedOnce,
      projectFlags,
    )
    const showCont = shouldShowContent(loadedOnce, filters, isLoading)
    const showEmpty = shouldShowEmptyState(isLoading, loadedOnce, showCont)
    const showCreateBtn = shouldShowCreateButton(loadedOnce, filters)

    return {
      shouldShowCreateButton: showCreateBtn,
      showContent: showCont,
      showEmptyState: showEmpty,
      showInitialLoader: showInitLoader,
    }
  }, [isLoading, loadedOnce, projectFlags, filters])

  return {
    ...displayFlags,
    loadedOnce,
  }
}
