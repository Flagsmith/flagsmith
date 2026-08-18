import { PagedResponse } from './types/responses'

export type CursorPagedRequest = {
  page_size?: number
  // Stack of cursors the calling component has stepped through to reach the
  // current page. The last entry is the cursor for the current page; empty or
  // undefined means the first page.
  pages?: (string | undefined)[]
}

// Normalises a cursor/keyset-paginated response into the `next`/`previous`
// sentinels that <Paging> understands. The cursor stack (`pages`) is owned by
// the calling component and threaded through the request; this transform only
// derives prev/next availability:
//   - `next`: a full page implies there may be more rows.
//   - `previous`: a non-empty cursor stack means we are past the first page.
export default function transformCursorPaging<T, R extends PagedResponse<T>>(
  req: CursorPagedRequest,
  res: R,
): R {
  const pageSize = req.page_size ?? 10
  return {
    ...res,
    next: res.results.length < pageSize ? undefined : '1',
    previous: req.pages?.length ? '1' : undefined,
  }
}
