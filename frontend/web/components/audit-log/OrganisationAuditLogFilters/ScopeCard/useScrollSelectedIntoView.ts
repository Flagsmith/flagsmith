import { RefObject, useLayoutEffect } from 'react'

// Centres the selected row when the list first shows, so it isn't hidden
// below the scroll. rowCount re-runs it once the rows have loaded.
export default function useScrollSelectedIntoView(
  listRef: RefObject<HTMLElement | null>,
  rowCount: number,
) {
  useLayoutEffect(() => {
    const list = listRef.current
    const row = list
      ?.querySelector('input:checked')
      ?.closest<HTMLElement>('label')
    if (!list || !row) return
    list.scrollTop = row.offsetTop - (list.clientHeight - row.offsetHeight) / 2
  }, [listRef, rowCount])
}
