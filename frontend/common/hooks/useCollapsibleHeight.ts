import { CSSProperties, useEffect, useRef, useState } from 'react'

/**
 * Hook for animating height transitions (expand/collapse).
 *
 * Uses a double requestAnimationFrame on collapse to ensure the browser
 * paints the current scrollHeight before transitioning to 0.
 */
const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

export default function useCollapsibleHeight(open: boolean) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number | undefined>(open ? undefined : 0)
  const lastOpen = useRef(open)

  useEffect(() => {
    // Only animate a change; measuring on mount would flash a closed body open.
    if (lastOpen.current === open) return
    lastOpen.current = open
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

  const style: CSSProperties = {
    height: height !== undefined ? `${height}px` : 'auto',
    overflow: height === undefined ? 'visible' : 'hidden',
    transition: prefersReducedMotion() ? 'none' : 'height 0.3s ease',
  }

  return { contentRef, style }
}
