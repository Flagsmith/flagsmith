import { useMemo } from 'react'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useProjectEnvironments } from './useProjectEnvironments'
import { buildApiFilterParams } from 'common/utils/featureFilterParams'
import type { FilterState } from 'common/types/featureFilters'

/**
 * Custom hook that combines filter state with RTK Query for fetching feature lists.
 *
 * This is the global replacement for the legacy `AppActions.getFeatures()` pattern.
 * It handles the transparent conversion of environment API key to database ID and
 * provides a consistent interface for filtered, paginated feature lists.
 *
 * @param filters - Current filter state (search, tags, archived, enabled, owners, etc.)
 * @param page - Current page number
 * @param environmentApiKey - The environment API key from RouteContext (e.g., "dev_abc123")
 * @param projectId - The project database ID
 * @returns RTK Query result with data, isLoading, isFetching states
 *
 * @example
 * ```tsx
 * // Basic usage
 * const { data, isLoading, isFetching } = useFeatureListWithFilters(
 *   filters,
 *   page,
 *   environmentApiKey,
 *   projectId,
 * )
 *
 * // With destructured results
 * const projectFlags = data?.results ?? []
 * const totalCount = data?.count ?? 0
 * ```
 *
 * @example
 * ```tsx
 * // Migration from legacy AppActions.getFeatures()
 * // BEFORE:
 * AppActions.getFeatures(projectId, environmentId, true, search, sort, page, filters)
 *
 * // AFTER:
 * const { data, isLoading } = useFeatureListWithFilters(
 *   filterState,  // Structured filter object
 *   page,
 *   environmentApiKey,
 *   projectId,
 * )
 * ```
 */
export function useFeatureListWithFilters(
  filters: FilterState,
  page: number,
  environmentApiKey: string | undefined,
  projectId: number | undefined,
) {
  // Fetch project and environments to enable API key → DB ID conversion
  const { getEnvironmentIdFromKey, isLoading: isLoadingEnvironments } =
    useProjectEnvironments(projectId!)

  // Convert environment API key to numeric database ID
  const environmentId = useMemo(() => {
    if (!environmentApiKey || !getEnvironmentIdFromKey) return undefined
    return getEnvironmentIdFromKey(environmentApiKey)
  }, [environmentApiKey, getEnvironmentIdFromKey])

  // Build API parameters with converted environment ID
  const apiParams = useMemo(() => {
    if (!environmentId || !projectId) return null

    return buildApiFilterParams(filters, page, environmentId, projectId)
  }, [filters, page, environmentId, projectId])

  // Execute RTK Query with skip condition
  return useGetFeatureListQuery(
    apiParams || ({} as any), // Fallback for TypeScript - will be skipped anyway
    {
      skip: !apiParams || isLoadingEnvironments,
    },
  )
}
