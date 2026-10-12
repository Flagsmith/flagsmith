import { PagedResponse } from 'common/types/responses'

type PageResult<T, E> = { data?: PagedResponse<T>; error?: E }

// DRF pages lists at 10 by default, and not every endpoint takes a page_size.
export const fetchAllPages = async <T, E>(
  fetchPage: (page: number) => Promise<PageResult<T, E>>,
): Promise<{ data: T[] } | { error: E }> => {
  const results: T[] = []

  for (let page = 1; ; page++) {
    const { data, error } = await fetchPage(page)
    if (error !== undefined) return { error }
    results.push(...(data?.results ?? []))
    if (!data?.next) return { data: results }
  }
}
