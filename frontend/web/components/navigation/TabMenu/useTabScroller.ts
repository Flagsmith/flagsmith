import { RefObject, useEffect, useLayoutEffect, useState } from 'react'

type ScrollEdges = {
  canScrollStart: boolean
  canScrollEnd: boolean
}

// Horizontally scrolling tabs: reports which edges have more tabs behind them
// and keeps the active tab in view.
export const useTabScroller = (
  ref: RefObject<HTMLDivElement | null>,
  enabled: boolean,
  activeIndex: number,
  tabCount: number,
): ScrollEdges => {
  const [edges, setEdges] = useState<ScrollEdges>({
    canScrollEnd: false,
    canScrollStart: false,
  })

  useLayoutEffect(() => {
    const el = ref.current
    if (!enabled || !el) return
    const update = () =>
      setEdges({
        canScrollEnd: el.scrollLeft + el.clientWidth < el.scrollWidth - 1,
        canScrollStart: el.scrollLeft > 1,
      })
    update()
    el.addEventListener('scroll', update, { passive: true })
    const observer =
      typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(update)
    // The tabs too: a tab that grows, such as with the unsaved dot, moves the
    // edges without resizing the row
    const watched = [el, ...Array.from(el.children)]
    watched.forEach((node) => observer?.observe(node))
    return () => {
      el.removeEventListener('scroll', update)
      observer?.disconnect()
    }
  }, [enabled, ref, tabCount])

  useEffect(() => {
    const el = ref.current
    const tab = el?.children.item(activeIndex)
    if (!enabled || !el || !(tab instanceof HTMLElement)) return
    const reduceMotion = window.matchMedia?.(
      '(prefers-reduced-motion: reduce)',
    ).matches
    // Next frame, so the new tab's content has rendered and can't cut it short
    const frame = requestAnimationFrame(() =>
      el.scrollTo({
        behavior: reduceMotion ? 'auto' : 'smooth',
        left: tab.offsetLeft - (el.clientWidth - tab.offsetWidth) / 2,
      }),
    )
    return () => cancelAnimationFrame(frame)
  }, [enabled, activeIndex, ref])

  return edges
}
