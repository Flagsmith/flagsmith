import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from './useProjectEnvironments'
import { buildApiFilterParams } from 'common/utils/featureFilterParams'
import type { FilterState } from 'common/types/featureFilters'

/**
 * Fetches filtered feature list, accepting environment API key instead of numeric ID.
 *
 * TODO: This wrapper will be removed once we standardize environmentId and environmentApiKey on RouteContext.
 */
export function useFeatureListWithApiKey(
  filters: FilterState,
  page: number,
  environmentApiKey: string | undefined,
  projectId: number | undefined,
): ReturnType<typeof useGetFeatureListQuery> {
  const { getEnvironmentIdFromKey, isLoading: isLoadingEnvironments } =
    useProjectEnvironments(projectId!)

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
