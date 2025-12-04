import { config } from 'common/config'
import Format from './format'
import type { FilterState, UrlParams } from 'common/types/featureFilters'
import type { TagStrategy } from 'common/types/responses'

/** Check if any filters are currently active. */
export function hasActiveFilters(filters: FilterState): boolean {
  return (
    (filters.tags && filters.tags.length > 0) ||
    filters.showArchived ||
    (filters.search !== null && filters.search.length > 0) ||
    filters.is_enabled !== null ||
    (filters.value_search && filters.value_search.length > 0) ||
    (filters.owners && filters.owners.length > 0) ||
    (filters.group_owners && filters.group_owners.length > 0)
  )
}

/** Converts filter state to URL query parameters. */
export function buildUrlParams(
  filters: FilterState,
  page: number,
): Record<string, string | number | boolean | undefined> {
  return {
    group_owners:
      filters.group_owners?.length > 0
        ? filters.group_owners.join(',')
        : undefined,
    is_archived: filters.showArchived || undefined,
    is_enabled: filters.is_enabled === null ? undefined : filters.is_enabled,
    owners: filters.owners?.length > 0 ? filters.owners.join(',') : undefined,
    page: page ?? 1,
    search: filters.search ?? '',
    sortBy: filters.sort.sortBy,
    sortOrder: filters.sort.sortOrder,
    tag_strategy: filters.tag_strategy,
    tags: filters.tags?.length > 0 ? filters.tags.join(',') : undefined,
    value_search: filters.value_search ?? undefined,
  }
}

/** Converts filter state to RTK Query API parameters. */
export function buildApiFilterParams(
  filters: FilterState,
  page: number,
  environmentId: number,
  projectId: number,
): {
  environmentId: number
  projectId: number
  page: number
  page_size: number
  search: string | null
  is_archived: boolean
  is_enabled: boolean | null
  owners: string | undefined
  group_owners: string | undefined
  tags: string | undefined
  tag_strategy: TagStrategy
  value_search: string | undefined
  sort_field: string
  sort_direction: 'ASC' | 'DESC'
} {
  return {
    environmentId,
    group_owners: filters.group_owners?.length
      ? filters.group_owners.join(',')
      : undefined,
    is_archived: filters.showArchived,
    is_enabled: filters.is_enabled,
    owners: filters.owners?.length ? filters.owners.join(',') : undefined,
    page,
    page_size: config.FEATURES_PAGE_SIZE,
    projectId,
    search: filters.search,
    sort_direction: filters.sort.sortOrder === 'asc' ? 'ASC' : 'DESC',
    sort_field: filters.sort.sortBy,
    tag_strategy: filters.tag_strategy,
    tags: filters.tags?.length ? filters.tags.join(',') : undefined,
    value_search: filters.value_search ?? undefined,
  }
}

/** Parses URL query parameters into FilterState with page number. */
export function getFiltersFromParams(
  params: UrlParams,
): FilterState & { page: number } {
  return {
    group_owners:
      typeof params.group_owners === 'string' && params.group_owners
        ? params.group_owners
            .split(',')
            .filter((v) => v)
            .map((v: string) => parseInt(v))
        : [],
    is_enabled: (() => {
      if (params.is_enabled === 'true') return true
      if (params.is_enabled === 'false') return false
      return null
    })(),
    owners:
      typeof params.owners === 'string' && params.owners
        ? params.owners
            .split(',')
            .filter((v) => v)
            .map((v: string) => parseInt(v))
        : [],
    page: params.page ? parseInt(params.page) : 1,
    search: params.search ?? null,
    showArchived: params.is_archived === 'true',
    sort: {
      label: Format.camelCase(params.sortBy ?? 'Name'),
      sortBy: params.sortBy ?? 'name',
      sortOrder: params.sortOrder ?? 'asc',
    },
    tag_strategy: params.tag_strategy ?? 'INTERSECTION',
    tags:
      typeof params.tags === 'string' && params.tags
        ? params.tags
            .split(',')
            .filter((v) => v)
            .map((v: string) => parseInt(v))
        : [],
    value_search:
      typeof params.value_search === 'string' ? params.value_search : '',
  }
}
