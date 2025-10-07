import { PagedResponse } from './types/responses'
import transformCorePaging from './transformCorePaging'
import { PagedRequest } from './types/requests'

// Fetches all pages in a given query
export async function recursiveServiceFetch<T>(
  baseQuery: (arg: unknown) => any,
  path: string,
  req: PagedRequest<any>,
): Promise<PagedResponse<T>> {
  let all: PagedResponse<T> | undefined = undefined
  let nextUrl: string | undefined
  const pageSize = req.page_size || 100
  do {
    const res = await baseQuery(nextUrl ? { url: nextUrl } : { req, url: path })
    if ('error' in res) throw res.error

    const page = res.data as PagedResponse<T>

    if (!all) {
      all = page
    } else {
      all = {
        ...page,
        results: all.results.concat(page.results),
      }
    }
    nextUrl = page?.next ?? undefined
  } while (nextUrl)

  return transformCorePaging(
    {
      ...req,
      pageSize,
    },
    all,
  )
}
