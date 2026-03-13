import { useEffect, useRef, useState } from 'react'

/**
 * Hook for animating height transitions (expand/collapse).
 *
 * Uses a double requestAnimationFrame on collapse to ensure the browser
 * paints the current scrollHeight before transitioning to 0.
 */
export default function useCollapsibleHeight(open: boolean) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number | undefined>(open ? undefined : 0)

  useEffect(() => {
    if (!contentRef.current) return
    if (open) {
      setHeight(contentRef.current.scrollHeight)
      const timer = setTimeout(() => setHeight(undefined), 300)
      return () => clearTimeout(timer)
    } else {
      setHeight(contentRef.current.scrollHeight)
      let innerFrameId: number
      const outerFrameId = requestAnimationFrame(() => {
        innerFrameId = requestAnimationFrame(() => {
          setHeight(0)
        })
      })
      return () => {
        cancelAnimationFrame(outerFrameId)
        cancelAnimationFrame(innerFrameId)
      }
    }
  }, [open])

  const style = {
    height: height !== undefined ? `${height}px` : 'auto',
    overflow: 'hidden' as const,
    transition: 'height 0.3s ease',
  }

  return { contentRef, style }
}
