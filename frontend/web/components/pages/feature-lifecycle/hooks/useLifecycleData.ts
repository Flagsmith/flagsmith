import { useEffect, useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetTagsQuery } from 'common/services/useTag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import FeatureListStore from 'common/stores/feature-list-store'
import type { ProjectFlag } from 'common/types/responses'
import type { Req } from 'common/types/requests'
import type { FilterState } from 'common/types/featureFilters'
import type { LifecycleCounts } from 'components/pages/feature-lifecycle/types'

type UseLifecycleDataOptions = {
  projectId: number
  environmentApiKey: string | undefined
  filters: FilterState
}

function totalCodeRefs(f: ProjectFlag): number {
  return (f.code_references_counts ?? []).reduce((sum, r) => sum + r.count, 0)
}

export function useLifecycleData({
  environmentApiKey,
  filters,
  projectId,
}: UseLifecycleDataOptions) {
  const { data: tags } = useGetTagsQuery({ projectId: `${projectId}` })

  const staleTagId = useMemo(
    () => tags?.find((t) => t.type === 'STALE')?.id,
    [tags],
  )
  const permanentTagIds = useMemo(
    () => new Set(tags?.filter((t) => t.is_permanent).map((t) => t.id)),
    [tags],
  )

  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const environmentId = environmentApiKey
    ? getEnvironmentIdFromKey(environmentApiKey)
    : undefined

  // Build base query params shared by both calls.
  // Uses getProjectFlags which recursively fetches all pages, so no
  // page/page_size needed. Lifecycle classification still happens
  // client-side based on code_references_counts (new vs live, stale vs
  // monitor/remove) since the backend doesn't support filtering by
  // code-reference presence.
  const baseParams = useMemo((): Req['getProjectFlags'] | null => {
    if (!environmentId) return null

    const params: Req['getProjectFlags'] = {
      environment: environmentId,
      is_archived: false,
      project: String(projectId),
      sort_direction: filters.sort.sortOrder,
      sort_field: filters.sort.sortBy,
      tag_strategy: filters.tag_strategy,
    }

    if (filters.search) params.search = filters.search
    if (filters.owners?.length) params.owners = filters.owners
    if (filters.group_owners?.length) params.group_owners = filters.group_owners
    if (filters.is_enabled !== null) params.is_enabled = filters.is_enabled
    if (filters.value_search) params.value_search = filters.value_search

    // Include user-selected tags (but not stale tag) for the "all" query
    const userTags = filters.tags ?? []
    if (userTags.length) params.tags = userTags.join(',')

    return params
  }, [environmentId, projectId, filters])

  // Query 1: All features (no stale tag filter) — for new, live, permanent
  const allQuery = useGetProjectFlagsQuery(baseParams ?? skipToken, {
    refetchOnMountOrArgChange: true,
  })

  // Query 2: Stale-tagged features — for stale, monitor, remove
  const staleParams = useMemo(() => {
    if (!baseParams || !staleTagId) return null
    const userTags = filters.tags ?? []
    const mergedTags = userTags.includes(staleTagId)
      ? userTags
      : [...userTags, staleTagId]
    return { ...baseParams, tags: mergedTags.join(',') }
  }, [baseParams, staleTagId, filters.tags])

  const staleQuery = useGetProjectFlagsQuery(staleParams ?? skipToken, {
    refetchOnMountOrArgChange: true,
  })

  // Extract refetch fns so eslint sees stable references
  const { refetch: refetchAll } = allQuery
  const { refetch: refetchStale } = staleQuery

  // Refetch on feature save/remove
  useEffect(() => {
    const onFeatureListChange = () => {
      refetchAll()
      refetchStale()
    }
    FeatureListStore.on('saved', onFeatureListChange)
    FeatureListStore.on('removed', onFeatureListChange)
    return () => {
      FeatureListStore.off('saved', onFeatureListChange)
      FeatureListStore.off('removed', onFeatureListChange)
    }
  }, [refetchAll, refetchStale])

  const isPermanent = useMemo(
    () => (f: ProjectFlag) => f.tags.some((t) => permanentTagIds.has(t)),
    [permanentTagIds],
  )

  // Pre-filter arrays from query 1
  const newFlags = useMemo(() => {
    if (!allQuery.data?.results || !staleTagId) return []
    return allQuery.data.results.filter(
      (f) =>
        !f.tags.includes(staleTagId) &&
        !isPermanent(f) &&
        totalCodeRefs(f) === 0,
    )
  }, [allQuery.data?.results, staleTagId, isPermanent])

  const liveFlags = useMemo(() => {
    if (!allQuery.data?.results || !staleTagId) return []
    return allQuery.data.results.filter(
      (f) =>
        !f.tags.includes(staleTagId) && !isPermanent(f) && totalCodeRefs(f) > 0,
    )
  }, [allQuery.data?.results, staleTagId, isPermanent])

  const permanentFlags = useMemo(() => {
    if (!allQuery.data?.results) return []
    return allQuery.data.results.filter(isPermanent)
  }, [allQuery.data?.results, isPermanent])

  // Pre-filter arrays from query 2
  const staleFlags = useMemo(() => {
    if (!staleQuery.data?.results) return []
    return staleQuery.data.results.filter(
      (f) => !isPermanent(f) && totalCodeRefs(f) > 0,
    )
  }, [staleQuery.data?.results, isPermanent])

  const staleNoCodeFlags = useMemo(() => {
    if (!staleQuery.data?.results) return []
    return staleQuery.data.results.filter(
      (f) => !isPermanent(f) && totalCodeRefs(f) === 0,
    )
  }, [staleQuery.data?.results, isPermanent])

  // Counts (monitor/remove will be overridden by useEvaluationCounts)
  const counts: LifecycleCounts = useMemo(
    () => ({
      live: liveFlags.length,
      new: newFlags.length,
      permanent: permanentFlags.length,
      stale: staleFlags.length,
    }),
    [
      newFlags.length,
      liveFlags.length,
      permanentFlags.length,
      staleFlags.length,
    ],
  )

  const isLoading = allQuery.isLoading || staleQuery.isLoading || !staleTagId
  const error = allQuery.error || staleQuery.error

  const refetch = useMemo(
    () => () => {
      refetchAll()
      refetchStale()
    },
    [refetchAll, refetchStale],
  )

  return {
    counts,
    error,
    isLoading,
    liveFlags,
    newFlags,
    permanentFlags,
    permanentTagIds,
    refetch,
    staleFlags,
    staleNoCodeFlags,
    staleTagId,
  }
}
