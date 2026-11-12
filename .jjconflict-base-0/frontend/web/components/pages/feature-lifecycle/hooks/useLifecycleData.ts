import { useEffect, useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import {
  useGetLifecycleStatusCountsQuery,
  useGetProjectFlagsQuery,
} from 'common/services/useProjectFlag'
import FeatureListStore from 'common/stores/feature-list-store'
import type { Req } from 'common/types/requests'
import type { FilterState } from 'common/types/featureFilters'
import { SECTION_TO_STAGE } from 'components/pages/feature-lifecycle/constants'
import type {
  LifecycleCounts,
  Section,
} from 'components/pages/feature-lifecycle/types'

type BaseOptions = {
  projectId: number
  environmentId: number | undefined
  filters: FilterState
}

// Filter params for the per-section list. The backend owns lifecycle
// classification, so no client-side tag/code-reference logic remains here.
function useFilterParams(filters: FilterState) {
  return useMemo(() => {
    const params: {
      search?: string | null
      tag_strategy: FilterState['tag_strategy']
      tags?: string
      is_archived: boolean
      value_search?: string | null
      is_enabled?: boolean | null
      owners?: number[]
      group_owners?: number[]
    } = {
      is_archived: false,
      tag_strategy: filters.tag_strategy,
    }
    if (filters.search) params.search = filters.search
    if (filters.owners?.length) params.owners = filters.owners
    if (filters.group_owners?.length) params.group_owners = filters.group_owners
    if (filters.is_enabled !== null) params.is_enabled = filters.is_enabled
    if (filters.value_search) params.value_search = filters.value_search
    if (filters.tags?.length) params.tags = filters.tags.join(',')
    return params
  }, [filters])
}

// Sidebar counts for every lifecycle stage in a single API call. The counts
// endpoint is environment-scoped and unfiltered — it reports the whole
// environment regardless of the active list filters.
export function useLifecycleCounts({
  environmentId,
}: {
  environmentId: number | undefined
}) {
  const query = useGetLifecycleStatusCountsQuery(
    environmentId ? { environment: environmentId } : skipToken,
    { refetchOnMountOrArgChange: true },
  )

  const { refetch } = query
  useEffect(() => {
    FeatureListStore.on('saved', refetch)
    FeatureListStore.on('removed', refetch)
    return () => {
      FeatureListStore.off('saved', refetch)
      FeatureListStore.off('removed', refetch)
    }
  }, [refetch])

  const counts: LifecycleCounts = useMemo(() => {
    const data = query.data
    if (!data) return {}
    return {
      live: data.live,
      monitor: data.needs_monitoring,
      new: data.new,
      permanent: data.permanent,
      remove: data.to_remove,
      stale: data.stale,
    }
  }, [query.data])

  return {
    counts,
    error: query.error,
    isLoading: query.isLoading || query.isFetching,
  }
}

// Flags for the currently active section, classified by the backend.
export function useLifecycleSectionFlags({
  environmentId,
  filters,
  projectId,
  section,
}: BaseOptions & { section: Section }) {
  const filterParams = useFilterParams(filters)

  const params = useMemo((): Req['getProjectFlags'] | null => {
    if (!environmentId) return null
    return {
      environment: environmentId,
      lifecycle_stage: SECTION_TO_STAGE[section],
      project: String(projectId),
      sort_direction: filters.sort.sortOrder,
      sort_field: filters.sort.sortBy,
      ...filterParams,
    }
  }, [environmentId, section, projectId, filters.sort, filterParams])

  const query = useGetProjectFlagsQuery(params ?? skipToken, {
    refetchOnMountOrArgChange: true,
  })

  const { refetch } = query
  useEffect(() => {
    FeatureListStore.on('saved', refetch)
    FeatureListStore.on('removed', refetch)
    return () => {
      FeatureListStore.off('saved', refetch)
      FeatureListStore.off('removed', refetch)
    }
  }, [refetch])

  return {
    error: query.error,
    flags: query.data?.results ?? [],
    isLoading: query.isLoading || query.isFetching,
  }
}
