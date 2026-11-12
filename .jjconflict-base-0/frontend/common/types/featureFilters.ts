import type { TagStrategy } from './responses'
import type { SortValue } from 'components/tables/TableSortFilter'

/** Raw URL parameters for feature list filtering. */
export type UrlParams = Record<string, string | string[] | undefined>

/** Structured filter configuration for querying feature lists. */
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
