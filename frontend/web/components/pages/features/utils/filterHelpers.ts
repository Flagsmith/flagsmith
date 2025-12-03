/**
 * Pure utility functions for filter transformations on the Features page.
 * These functions handle converting between filter state, URL params, and API params.
 */

import type { FilterState } from 'components/pages/features/components/FeaturesTableFilters'
import { config } from 'common/config'

/**
 * Check if any filters are currently active.
 * Uses simple boolean checks instead of deep equality comparison for better performance.
 *
 * @param filters - The current filter state
 * @returns true if any filter is active, false otherwise
 */
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

/**
 * Build URL query parameters from filter state.
 * Converts filter state into a format suitable for URL serialization.
 *
 * @param filters - The current filter state
 * @param page - The current page number
 * @returns Object ready for URL parameter serialization
 */
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

/**
 * Build API filter parameters from filter state.
 * Converts filter state into the format expected by the RTK Query API call.
 *
 * @param filters - The current filter state
 * @param page - The current page number
 * @param environmentId - The environment ID
 * @param projectId - The project ID
 * @returns Object ready for RTK Query API call
 */
export function buildApiFilterParams(
  filters: FilterState,
  page: number,
  environmentId: string,
  projectId: number,
): {
  environmentId: string
  projectId: number
  page: number
  page_size: number
  search: string | null
  is_archived: boolean
  is_enabled: boolean | null
  owners: string | undefined
  group_owners: string | undefined
  tags: string | undefined
  tag_strategy: string
  value_search: string | undefined
  sort_field: string
  sort_direction: 'ASC' | 'DESC'
} {
  return {
    environmentId,
    group_owners: filters.group_owners.length
      ? filters.group_owners.join(',')
      : undefined,
    is_archived: filters.showArchived,
    is_enabled: filters.is_enabled,
    owners: filters.owners.length ? filters.owners.join(',') : undefined,
    page,
    page_size: config.FEATURES_PAGE_SIZE,
    projectId,
    search: filters.search,
    sort_direction: filters.sort.sortOrder === 'asc' ? 'ASC' : 'DESC',
    sort_field: filters.sort.sortBy,
    tag_strategy: filters.tag_strategy,
    tags: filters.tags.length ? filters.tags.join(',') : undefined,
    value_search: filters.value_search ?? undefined,
  }
}
