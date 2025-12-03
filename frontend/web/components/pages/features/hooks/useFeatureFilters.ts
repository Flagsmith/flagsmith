import { useState, useMemo, useCallback, useEffect } from 'react'
import type { History } from 'history'
import type { FilterState } from 'components/pages/features/components/FeaturesTableFilters'
import type { UrlParams } from 'components/pages/features/types'
import Utils from 'common/utils/utils'
import Format from 'common/utils/format'
import {
  hasActiveFilters,
  buildUrlParams,
} from 'components/pages/features/utils/filterHelpers'

/**
 * Converts URL query parameters to FilterState object.
 * Handles parsing of arrays, booleans, and sort configuration from URL params.
 *
 * @param params - URL query parameters as key-value pairs
 * @returns Structured filter state object
 */
export const getFiltersFromParams = (params: UrlParams): FilterState => {
  return {
    group_owners:
      typeof params.group_owners === 'string'
        ? params.group_owners.split(',').map((v: string) => parseInt(v))
        : [],
    is_enabled: (() => {
      if (params.is_enabled === 'true') return true
      if (params.is_enabled === 'false') return false
      return null
    })(),
    owners:
      typeof params.owners === 'string'
        ? params.owners.split(',').map((v: string) => parseInt(v))
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
      typeof params.tags === 'string'
        ? params.tags.split(',').map((v: string) => parseInt(v))
        : [],
    value_search:
      typeof params.value_search === 'string' ? params.value_search : '',
  }
}

/**
 * Custom hook for managing feature list filters and pagination state.
 *
 * Syncs filter state with URL query parameters bidirectionally:
 * - Initializes filters from URL on mount
 * - Updates URL whenever filters change
 * - Preserves filter state across page refreshes
 *
 * @param history - React Router history object for URL manipulation
 * @returns Object containing filters, pagination state, and filter management functions
 *
 * @example
 * ```tsx
 * const { filters, page, handleFilterChange, goToPage } = useFeatureFilters(history)
 *
 * // Update search filter
 * handleFilterChange({ search: 'my-feature' })
 *
 * // Navigate to next page
 * goToPage(page + 1)
 * ```
 */
export function useFeatureFilters(history: History): {
  filters: FilterState
  page: number
  hasFilters: boolean
  handleFilterChange: (updates: Partial<FilterState>) => void
  clearFilters: () => void
  goToPage: (newPage: number) => void
} {
  const initialFilters = useMemo(
    () => getFiltersFromParams(Utils.fromParam()),
    [],
  )

  const [filters, setFilters] = useState<FilterState>(initialFilters)
  const [page, setPage] = useState<number>(initialFilters.page)

  const updateURLParams = useCallback(() => {
    const currentParams = Utils.fromParam()
    if (!currentParams.feature) {
      const urlParams = buildUrlParams(filters, page)
      history.replace(
        `${document.location.pathname}?${Utils.toParam(urlParams)}`,
      )
    }
  }, [filters, page, history])

  useEffect(() => {
    updateURLParams()
  }, [updateURLParams])

  const handleFilterChange = useCallback((updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }))
    setPage(1)
  }, [])

  const clearFilters = useCallback(() => {
    history.replace(document.location.pathname)
    const newFilters = getFiltersFromParams({})
    setFilters(newFilters)
    setPage(1)
  }, [history])

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

  return {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters: hasActiveFilters(filters),
    page,
  }
}
