import { PagedResponse } from 'common/types/responses'

type PageResult<T> = { data?: PagedResponse<T>; error?: unknown }

// DRF pages lists at 10 by default, and not every endpoint takes a page_size.
export const fetchAllPages = async <T>(
  fetchPage: (page: number) => Promise<PageResult<T>>,
): Promise<{ data: T[] } | { error: unknown }> => {
  const results: T[] = []

  for (let page = 1; ; page++) {
    const { data, error } = await fetchPage(page)
    if (error || !data) return { error }
    results.push(...data.results)
    if (!data.next) return { data: results }
  }
}
