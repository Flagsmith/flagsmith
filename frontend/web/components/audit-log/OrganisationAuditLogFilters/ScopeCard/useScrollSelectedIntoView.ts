import { RefObject, useLayoutEffect } from 'react'

// Centres the selected row when the list first shows, so it isn't hidden
// below the scroll.
export default function useScrollSelectedIntoView(
  listRef: RefObject<HTMLElement | null>,
) {
  useLayoutEffect(() => {
    const list = listRef.current
    const row = list
      ?.querySelector('input:checked')
      ?.closest<HTMLElement>('label')
    if (!list || !row) return
    list.scrollTop = row.offsetTop - (list.clientHeight - row.offsetHeight) / 2
  }, [listRef])
}
