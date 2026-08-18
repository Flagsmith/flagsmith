import sortBy from 'lodash/sortBy'
import type { FilterState } from 'common/types/featureFilters'
import type { ProjectFlag, TagStrategy } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'

/**
 * Client-side filter matching for ProjectFlag objects.
 *
 * Use this when filtering locally-held data (e.g. CompareEnvironments which
 * fetches all flags from two environments). For server-side filtering, use
 * buildApiFilterParams from featureFilterParams.ts instead.
 */
export function matchesProjectFlagFilters(
  projectFlag: ProjectFlag,
  filters: FilterState,
  tagStrategy: TagStrategy,
): boolean {
  // Archived filter
  if (!filters.showArchived && projectFlag.is_archived) {
    return false
  }

  // Search filter
  if (filters.search) {
    const searchLower = filters.search.toLowerCase()
    if (!projectFlag.name.toLowerCase().includes(searchLower)) {
      return false
    }
  }

  // Tags filter
  if (filters.tags.length > 0) {
    const featureTags = projectFlag.tags || []

    // Empty string in tags array means "no tags" filter
    if (filters.tags.includes('')) {
      if (featureTags.length > 0) {
        return false
      }
    } else {
      const tagIds = filters.tags.filter((t) => t !== '') as number[]
      if (tagIds.length > 0) {
        if (tagStrategy === 'INTERSECTION') {
          if (!tagIds.every((tagId) => featureTags.includes(tagId))) {
            return false
          }
        } else if (!tagIds.some((tagId) => featureTags.includes(tagId))) {
          return false
        }
      }
    }
  }

  // Owners filter
  if (filters.owners.length > 0) {
    const ownerIds = projectFlag.owners?.map((o) => o.id) || []
    if (!filters.owners.some((id) => ownerIds.includes(id))) {
      return false
    }
  }

  // Group owners filter
  if (filters.group_owners.length > 0) {
    const groupIds = projectFlag.group_owners?.map((g) => g.id) || []
    if (!filters.group_owners.some((id) => groupIds.includes(id))) {
      return false
    }
  }

  return true
}

/**
 * Client-side sort for ProjectFlag objects.
 */
export function sortProjectFlags<T extends { projectFlag: ProjectFlag }>(
  items: T[],
  sortBy_: FilterState['sort']['sortBy'],
  sortOrder: SortOrder,
): T[] {
  const sorted =
    sortBy_ === 'created_date'
      ? sortBy(items, (f) => f.projectFlag.created_date)
      : sortBy(items, (f) => f.projectFlag.name.toLowerCase())

  return sortOrder === SortOrder.DESC ? sorted.reverse() : sorted
}
