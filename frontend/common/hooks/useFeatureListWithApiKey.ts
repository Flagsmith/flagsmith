import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useProjectEnvironments } from './useProjectEnvironments'
import { buildApiFilterParams } from 'common/utils/featureFilterParams'
import type { FilterState } from 'common/types/featureFilters'

/**
 * Fetches filtered feature list, accepting environment API key instead of numeric ID.
 *
 * This hook bridges the gap between routing (which uses API keys) and the API
 * (which expects numeric environment IDs). It wraps useGetFeatureListQuery and
 * delegates the API key → numeric ID conversion to buildApiFilterParams.
 *
 * TODO: This hook will be simplified once environmentNumericId is added to RouteContext.
 * See: FEATURES_MIGRATION_FOLLOWUP.md - PR #1
 * When RouteContext provides the numeric ID directly, components can call
 * useGetFeatureListQuery directly without this wrapper.
 *
 * @param filters - Filter state for the feature list
 * @param page - Current page number
 * @param environmentApiKey - Environment API key from router context (string)
 * @param projectId - Project ID
 * @returns RTK Query result with feature list data
 */
export function useFeatureListWithApiKey(
  filters: FilterState,
  page: number,
  environmentApiKey: string | undefined,
  projectId: number | undefined,
) {
  const { getEnvironmentIdFromKey, isLoading: isLoadingEnvironments } =
    useProjectEnvironments(projectId!)

  // Build API filter parameters (includes API key → ID conversion)
  const apiParams = useMemo(() => {
    if (!environmentApiKey || !projectId || !getEnvironmentIdFromKey) {
      return null
    }
    return buildApiFilterParams(
      filters,
      page,
      environmentApiKey,
      projectId,
      getEnvironmentIdFromKey,
    )
  }, [filters, page, environmentApiKey, projectId, getEnvironmentIdFromKey])

  return useGetFeatureListQuery(apiParams ?? skipToken, {
    refetchOnMountOrArgChange: true,
    skip: isLoadingEnvironments,
  })
}
