import { FEATURES_PAGE_SIZE } from 'common/services/useProjectFlag'
import Format from './format'
import type { FilterState, UrlParams } from 'common/types/featureFilters'
import { SortOrder } from 'common/types/requests'
import { TagStrategy } from 'common/types/responses'

/**
 * Function type for resolving environment API keys to numeric IDs.
 * Used to bridge routing layer (API keys) with API layer (numeric IDs).
 */
export type EnvironmentIdResolver = (apiKey: string) => number | undefined

/** Converts array to comma-separated string, or undefined if empty */
function joinArrayOrUndefined(
  arr: (string | number)[] | undefined,
): string | undefined {
  if (!arr || arr.length === 0) return undefined
  return arr.join(',')
}

/** Parses comma-separated string into number array */
function parseIntArray(value: string | string[] | undefined): number[] {
  if (!value || typeof value !== 'string') return []
  return value
    .split(',')
    .filter((v) => v)
    .map((v) => parseInt(v, 10))
}

/** Normalizes UI sort order to API format */
function normalizeSortDirection(sortOrder: SortOrder | null): SortOrder {
  return sortOrder === SortOrder.ASC ? SortOrder.ASC : SortOrder.DESC
}

/** Parses boolean from URL param */
function parseBooleanParam(
  value: string | string[] | undefined,
): boolean | null {
  if (value === 'true') return true
  if (value === 'false') return false
  return null
}

/** Parses sort order from URL param, defaulting to ASC */
function parseSortOrder(value: string | string[] | undefined): SortOrder {
  if (typeof value === 'string' && value.toLowerCase() === 'desc') {
    return SortOrder.DESC
  }
  return SortOrder.ASC
}

/** Parses string from URL param, returns default if invalid */
function parseStringParam(
  value: string | string[] | undefined,
  defaultValue: string,
): string {
  if (typeof value === 'string') return value
  return defaultValue
}

/** Parses page number from URL param, defaulting to 1 */
function parsePageNumber(value: string | string[] | undefined): number {
  if (typeof value === 'string') {
    const parsed = parseInt(value, 10)
    return isNaN(parsed) ? 1 : parsed
  }
  return 1
}

/** Check if any filters are currently active. */
export function hasActiveFilters(filters: FilterState): boolean {
  return !!(
    filters.tags?.length ||
    filters.showArchived ||
    filters.search?.length ||
    filters.is_enabled !== null ||
    filters.value_search?.length ||
    filters.owners?.length ||
    filters.group_owners?.length
  )
}

/** Converts filter state to URL query parameters. */
export function buildUrlParams(
  filters: FilterState,
  page: number,
): Record<string, string | number | boolean | undefined> {
  return {
    group_owners: joinArrayOrUndefined(filters.group_owners),
    is_archived: filters.showArchived ? 'true' : 'false',
    is_enabled: filters.is_enabled === null ? undefined : filters.is_enabled,
    owners: joinArrayOrUndefined(filters.owners),
    page: page ?? 1,
    search: filters.search || undefined,
    sortBy: filters.sort.sortBy,
    sortOrder: filters.sort.sortOrder === SortOrder.DESC ? 'desc' : 'asc',
    tag_strategy: filters.tag_strategy,
    tags: joinArrayOrUndefined(filters.tags),
    value_search: filters.value_search || undefined,
  }
}

/**
 * Converts filter state to RTK Query API parameters.
 *
 * TODO: getEnvironmentIdFromKey callback is temporary
 * Once RouteContext provides environmentID and environmentApiKey, this can accept the numeric environmentID directly.
 */
export function buildApiFilterParams(
  filters: FilterState,
  page: number,
  environmentApiKey: string,
  projectId: number,
  getEnvironmentIdFromKey: EnvironmentIdResolver,
) {
  const environmentId = getEnvironmentIdFromKey(environmentApiKey)
  if (!environmentId) {
    return null
  }

  const groupOwners = joinArrayOrUndefined(filters.group_owners)
  const owners = joinArrayOrUndefined(filters.owners)
  const tags = joinArrayOrUndefined(filters.tags)
  const sortDirection = normalizeSortDirection(filters.sort.sortOrder)

  const params: Record<string, string | number | boolean> = {
    environmentId: String(environmentId),
    page,
    page_size: FEATURES_PAGE_SIZE,
    projectId,
    sort_direction: sortDirection,
    sort_field: filters.sort.sortBy,
    tag_strategy: filters.tag_strategy,
  }

  params.is_archived = filters.showArchived ? 'true' : 'false'
  if (groupOwners) params.group_owners = groupOwners
  if (filters.is_enabled !== null) params.is_enabled = filters.is_enabled
  if (owners) params.owners = owners
  if (filters.search) params.search = filters.search
  if (tags) params.tags = tags
  if (filters.value_search) params.value_search = filters.value_search

  return params
}

/** Parses URL query parameters into FilterState with page number. */
export function getFiltersFromParams(
  params: UrlParams,
): FilterState & { page: number } {
  const sortBy = parseStringParam(params.sortBy, 'name')
  const sortOrder = parseSortOrder(params.sortOrder)
  const search = parseStringParam(params.search, '')

  return {
    group_owners: parseIntArray(params.group_owners),
    is_enabled: parseBooleanParam(params.is_enabled),
    owners: parseIntArray(params.owners),
    page: parsePageNumber(params.page),
    search: search || null,
    showArchived: params.is_archived === 'true',
    sort: {
      label: Format.camelCase(sortBy),
      sortBy,
      sortOrder,
    },
    tag_strategy:
      params.tag_strategy === TagStrategy.UNION
        ? TagStrategy.UNION
        : TagStrategy.INTERSECTION,
    tags: parseIntArray(params.tags),
    value_search: parseStringParam(params.value_search, '') || null,
  }
}
