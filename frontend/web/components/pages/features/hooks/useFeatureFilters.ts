import { useState, useMemo, useCallback, useEffect } from 'react'
import { isEqual } from 'lodash'
import type { History } from 'history'
import type { FilterState } from 'components/pages/features/components/FeaturesTableFilters'
import type { UrlParams } from 'components/pages/features/types'
import Format from 'common/utils/format'

const getFiltersFromParams = (params: UrlParams) => {
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
    search: params.search || null,
    showArchived: params.is_archived === 'true',
    sort: {
      label: Format.camelCase(params.sortBy || 'Name'),
      sortBy: params.sortBy || 'name',
      sortOrder: params.sortOrder || 'asc',
    },
    tag_strategy: params.tag_strategy || 'INTERSECTION',
    tags:
      typeof params.tags === 'string'
        ? params.tags.split(',').map((v: string) => parseInt(v))
        : [],
    value_search:
      typeof params.value_search === 'string' ? params.value_search : '',
  }
}

export function useFeatureFilters(history: History) {
  const initialFilters = useMemo(
    () => getFiltersFromParams(Utils.fromParam()),
    [],
  )

  const [filters, setFilters] = useState<FilterState>(initialFilters)
  const [page, setPage] = useState<number>(initialFilters.page)

  const updateURLParams = useCallback(() => {
    const currentParams = Utils.fromParam()
    if (!currentParams.feature) {
      const urlParams = {
        group_owners: filters.group_owners?.join(',') || undefined,
        is_archived: filters.showArchived || undefined,
        is_enabled:
          filters.is_enabled === null ? undefined : filters.is_enabled,
        owners: filters.owners?.join(',') || undefined,
        page: page || 1,
        search: filters.search || '',
        sortBy: filters.sort.sortBy,
        sortOrder: filters.sort.sortOrder,
        tag_strategy: filters.tag_strategy,
        tags: filters.tags?.join(',') || undefined,
        value_search: filters.value_search || undefined,
      }
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

  const params = Utils.fromParam()
  const hasFilters = !isEqual(
    getFiltersFromParams({ ...params, page: '1' }),
    getFiltersFromParams({ page: '1' }),
  )

  return {
    clearFilters,
    filters,
    goToPage,
    handleFilterChange,
    hasFilters,
    page,
  }
}
