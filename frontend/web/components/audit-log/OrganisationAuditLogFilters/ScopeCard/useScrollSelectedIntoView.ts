import { RefObject, useLayoutEffect } from 'react'

// The list scrolls in the popover, but in the phone sheet the sheet scrolls.
const getScroller = (el: HTMLElement): HTMLElement | null => {
  for (let node: HTMLElement | null = el; node; node = node.parentElement) {
    const { overflowY } = getComputedStyle(node)
    const canScroll = overflowY === 'auto' || overflowY === 'scroll'
    if (canScroll && node.scrollHeight > node.clientHeight) return node
  }
  return null
}

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
    const scroller = list && getScroller(list)
    if (!row || !scroller) return
    const offset =
      row.getBoundingClientRect().top - scroller.getBoundingClientRect().top
    scroller.scrollTop +=
      offset - (scroller.clientHeight - row.offsetHeight) / 2
  }, [listRef, rowCount])
}
