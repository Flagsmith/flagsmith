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
 * Manages feature filters with bidirectional URL synchronization.
 * FeaturesPage-specific implementation.
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

  const handleFilterChange = (updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }))
    setPage(1)
  }

  const clearFilters = useCallback(() => {
    history.replace(document.location.pathname)
    const newFilters = getFiltersFromParams({})
    setFilters(newFilters)
    setPage(1)
  }, [history])

  const goToPage = (newPage: number) => {
    setPage(newPage)
  }

  return {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters: hasActiveFilters(filters),
    page,
  }
}
