import { PagedResponse } from 'common/types/responses'

// Fetches every page of a paginated endpoint through an RTK Query baseQuery,
// following `next` links and concatenating `results`. Returns the queryFn
// contract: `{ data }` with the merged response, or `{ error }` on failure.
export function recursivePageGet<T>(
  url: string,
  parentRes: null | PagedResponse<T>,
  baseQuery: (arg: unknown) => any, // matches rtk types,
): Promise<{ data: PagedResponse<T> } | { error: any }> {
  return baseQuery({
    method: 'GET',
    url,
  }).then((res: { data?: PagedResponse<T>; error?: any }) => {
    if (res.error || !res.data) {
      return res
    }
    const response = parentRes
      ? { ...res.data, results: parentRes.results.concat(res.data.results) }
      : res.data
    if (response.next) {
      return recursivePageGet(response.next, response, baseQuery)
    }
    return { data: response }
  })
}
