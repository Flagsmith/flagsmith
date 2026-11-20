import { RefObject, useLayoutEffect } from 'react'

// rowCount re-runs it once the rows have loaded.
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
