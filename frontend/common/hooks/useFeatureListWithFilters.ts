import { useMemo } from 'react'
import { useGetFeatureListQuery } from 'common/services/useFeatureList'
import { useProjectEnvironments } from './useProjectEnvironments'
import { buildApiFilterParams } from 'common/utils/featureFilterParams'
import type { FilterState } from 'common/types/featureFilters'

/** Fetches filtered feature list with automatic API key to ID conversion. */
export function useFeatureListWithFilters(
  filters: FilterState,
  page: number,
  environmentApiKey: string | undefined,
  projectId: number | undefined,
) {
  const { getEnvironmentIdFromKey, isLoading: isLoadingEnvironments } =
    useProjectEnvironments(projectId!)

  const environmentId = useMemo(() => {
    if (!environmentApiKey || !getEnvironmentIdFromKey) return undefined
    return getEnvironmentIdFromKey(environmentApiKey)
  }, [environmentApiKey, getEnvironmentIdFromKey])

  const apiParams = useMemo(() => {
    if (!environmentId || !projectId) return null
    return buildApiFilterParams(filters, page, environmentId, projectId)
  }, [filters, page, environmentId, projectId])

  return useGetFeatureListQuery(apiParams || ({} as any), {
    refetchOnMountOrArgChange: true,
    skip: !apiParams || isLoadingEnvironments,
  })
}
