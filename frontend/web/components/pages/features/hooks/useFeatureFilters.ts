import { useState, useMemo, useCallback, useEffect } from 'react'
import type { History } from 'history'
import type { FilterState } from 'common/types/featureFilters'
import {
  hasActiveFilters,
  buildUrlParams,
  getFiltersFromParams,
} from 'common/utils/featureFilterParams'
import Utils from 'common/utils/utils'

/**
 * Custom hook for managing feature list filters and pagination state.
 *
 * This hook is **FeaturesPage-specific** and handles bidirectional URL synchronization.
 * It composes global filter utilities with page-specific URL management logic.
 *
 * Syncs filter state with URL query parameters bidirectionally:
 * - Initializes filters from URL on mount
 * - Updates URL whenever filters change
 * - Preserves filter state across page refreshes
 * - Skips URL updates when viewing a single feature (feature detail view)
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
    // FeaturesPage-specific: Skip URL update when viewing single feature detail
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
