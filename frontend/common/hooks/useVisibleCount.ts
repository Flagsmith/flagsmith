// hooks/useVisibleCount.ts
import { useState, useLayoutEffect, RefObject } from 'react'

const GAP_MULTIPLIER = 5 // Assuming a spacer unit. Adjust if your system is different.

type UseVisibleCountOptions = {
  outerContainerRef: RefObject<HTMLDivElement>
  itemsContainerRef: RefObject<HTMLDivElement>
  itemCount: number
  gap: number
  extraWidth: number
  force?: boolean
}

export const useVisibleCount = ({
  extraWidth,
  force,
  gap,
  itemCount,
  itemsContainerRef,
  outerContainerRef,
}: UseVisibleCountOptions) => {
  const [visibleCount, setVisibleCount] = useState(force ? 0 : itemCount)
  const [widths, setWidths] = useState<number[]>([])

  // Reset state when the items change
  useLayoutEffect(() => {
    if (force) {
      setVisibleCount(0)
      return
    }
    setWidths([])
    setVisibleCount(itemCount)
  }, [itemCount, force])

  // Measure the width of each child item
  useLayoutEffect(() => {
    if (force || widths.length > 0 || itemCount === 0) {
      return
    }

    const itemsCont = itemsContainerRef.current
    if (!itemsCont) return

    const childEls = Array.from(itemsCont.children) as HTMLElement[]
    const newWidths = childEls.map((el) => el.offsetWidth)
    setWidths(newWidths)
  }, [itemCount, force, widths.length, itemsContainerRef])

  // Calculate visible count based
  useLayoutEffect(() => {
    if (force || widths.length === 0) {
      return
    }

    const calculate = () => {
      const outerCont = outerContainerRef.current
      if (!outerCont) return

      const gapPx = gap * GAP_MULTIPLIER

      const sumWidths = (count: number) => {
        if (count === 0) return 0
        const totalWidths = widths
          .slice(0, count)
          .reduce((acc, w) => acc + w, 0)
        const totalGaps = (count > 1 ? count - 1 : 0) * gapPx
        return totalWidths + totalGaps
      }

      const containerWidth = outerCont.clientWidth

      // All items fit
      if (sumWidths(widths.length) <= containerWidth) {
        setVisibleCount(widths.length)
        return
      }

      // Reserve space for the overflow button and its gap
      const reserve = extraWidth + gapPx
      const maxWidth = containerWidth - reserve

      let count = 0
      while (count < widths.length && sumWidths(count + 1) <= maxWidth) {
        count++
      }
      setVisibleCount(count)
    }

    calculate()

    const ro = new ResizeObserver(calculate)
    if (outerContainerRef.current) {
      ro.observe(outerContainerRef.current)
    }
    return () => ro.disconnect()
  }, [widths, force, gap, itemCount, extraWidth, outerContainerRef])

  const isMeasuring = !force && widths.length === 0 && itemCount > 0

  return { isMeasuring, visibleCount }
}
