import { config } from 'common/config'
import Format from './format'
import type { FilterState, UrlParams } from 'common/types/featureFilters'
import { TagStrategy } from 'common/types/responses'

/**
 * Function type for resolving environment API keys to numeric IDs.
 * Used to bridge routing layer (API keys) with API layer (numeric IDs).
 */
export type EnvironmentIdResolver = (apiKey: string) => number | undefined

// ===== Helper Functions =====

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
    .map((v) => parseInt(v))
}

/** Normalizes UI sort order to API format */
function normalizeSortDirection(sortOrder: string | null): 'ASC' | 'DESC' {
  return sortOrder === 'asc' ? 'ASC' : 'DESC'
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
function parseSortOrder(value: string | string[] | undefined): 'asc' | 'desc' {
  if (typeof value === 'string' && value === 'desc') {
    return 'desc'
  }
  return 'asc'
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
    const parsed = parseInt(value)
    return isNaN(parsed) ? 1 : parsed
  }
  return 1
}

// ===== Exported Functions =====

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
    is_archived: filters.showArchived || undefined,
    is_enabled: filters.is_enabled === null ? undefined : filters.is_enabled,
    owners: joinArrayOrUndefined(filters.owners),
    page: page ?? 1,
    search: filters.search ?? '',
    sortBy: filters.sort.sortBy,
    sortOrder: filters.sort.sortOrder ?? 'asc',
    tag_strategy: filters.tag_strategy,
    tags: joinArrayOrUndefined(filters.tags),
    value_search: filters.value_search ?? undefined,
  }
}

/**
 * Converts filter state to RTK Query API parameters.
 *
 * This transformation function bridges the gap between the application's filter state
 * and the format expected by the feature list API endpoint. It handles:
 * - Environment API key → numeric ID conversion (via callback)
 * - Array to comma-separated string transformations (tags, owners, etc.)
 * - Sort order normalization (UI 'asc'/'desc' → API 'ASC'/'DESC')
 * - Pagination parameters
 *
 * TODO: The getEnvironmentIdFromKey callback parameter is temporary.
 * See: FEATURES_MIGRATION_FOLLOWUP.md - PR #1
 * Once RouteContext provides environmentNumericId directly, this function can accept
 * the numeric ID as a simple parameter instead of requiring a callback.
 *
 * @param filters - Application filter state
 * @param page - Current page number (1-indexed)
 * @param environmentApiKey - Environment API key from router (string)
 * @param projectId - Project ID
 * @param getEnvironmentIdFromKey - Function to resolve API key to numeric ID
 * @returns API request parameters, or null if environment ID cannot be resolved
 */
export function buildApiFilterParams(
  filters: FilterState,
  page: number,
  environmentApiKey: string,
  projectId: number,
  getEnvironmentIdFromKey: EnvironmentIdResolver,
) {
  // Convert environment API key to numeric ID
  const environmentId = getEnvironmentIdFromKey(environmentApiKey)
  if (!environmentId) {
    return null
  }

  return {
    environmentId: String(environmentId),
    group_owners: joinArrayOrUndefined(filters.group_owners),
    is_archived: filters.showArchived,
    is_enabled: filters.is_enabled,
    owners: joinArrayOrUndefined(filters.owners),
    page,
    page_size: config.FEATURES_PAGE_SIZE,
    projectId,
    search: filters.search,
    sort_direction: normalizeSortDirection(filters.sort.sortOrder),
    sort_field: filters.sort.sortBy,
    tag_strategy: filters.tag_strategy,
    tags: joinArrayOrUndefined(filters.tags),
    value_search: filters.value_search ?? undefined,
  }
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
    value_search: parseStringParam(params.value_search, ''),
  }
}
