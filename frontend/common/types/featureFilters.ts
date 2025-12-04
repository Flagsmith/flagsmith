import type { TagStrategy } from './responses'
import type { SortValue } from 'components/tables/TableSortFilter'

/**
 * URL query parameters type for feature list filtering.
 * Represents the raw URL parameters before parsing into FilterState.
 */
export type UrlParams = Record<string, string | string[] | undefined>

/**
 * Feature list filter state.
 * Represents the structured filter configuration for querying feature lists.
 * Used across the application for consistent feature filtering behavior.
 */
export type FilterState = {
  search: string | null
  tags: (number | string)[]
  tag_strategy: TagStrategy
  showArchived: boolean
  is_enabled: boolean | null
  value_search: string
  owners: number[]
  group_owners: number[]
  sort: SortValue
}
