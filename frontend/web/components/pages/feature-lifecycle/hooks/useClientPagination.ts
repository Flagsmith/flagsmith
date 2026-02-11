import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Pagination } from 'components/pages/feature-lifecycle/types'

type UseClientPaginationOptions<T> = {
  items: T[]
  pageSize?: number
}

type UseClientPaginationResult<T> = {
  pageItems: T[]
  paging: Pagination
  goToPage: (page: number) => void
  nextPage: () => void
  prevPage: () => void
}

export function useClientPagination<T>({
  items,
  pageSize = 50,
}: UseClientPaginationOptions<T>): UseClientPaginationResult<T> {
  const [currentPage, setCurrentPage] = useState(1)

  // Reset to page 1 when items change
  const itemCount = items.length
  useEffect(() => {
    setCurrentPage(1)
  }, [itemCount])

  const totalPages = Math.max(1, Math.ceil(itemCount / pageSize))

  const pageItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return items.slice(start, start + pageSize)
  }, [items, currentPage, pageSize])

  const paging: Pagination = useMemo(
    () => ({
      count: itemCount,
      currentPage,
      next: currentPage < totalPages ? `page=${currentPage + 1}` : null,
      pageSize,
      previous: currentPage > 1 ? `page=${currentPage - 1}` : null,
    }),
    [itemCount, currentPage, totalPages, pageSize],
  )

  const nextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage((p) => p + 1)
    }
  }, [currentPage, totalPages])

  const prevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage((p) => p - 1)
    }
  }, [currentPage])

  return { goToPage: setCurrentPage, nextPage, pageItems, paging, prevPage }
}
