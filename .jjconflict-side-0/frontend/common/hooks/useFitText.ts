import { useLayoutEffect, useRef, useState } from 'react'

const MIN_FONT_SIZE = 14

// Shrinks the font from maxFontSize (down to MIN_FONT_SIZE) until the
// element's content fits its width, refitting when the element is resized.
// Pass undefined to leave the element alone.
export default function useFitText<T extends HTMLElement>(
  maxFontSize: number | undefined,
  text: string,
) {
  const ref = useRef<T>(null)
  const [fontSize, setFontSize] = useState(maxFontSize)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !maxFontSize) return
    const fit = () => {
      let size = maxFontSize
      el.style.fontSize = `${size}px`
      while (size > MIN_FONT_SIZE && el.scrollWidth > el.clientWidth) {
        size -= 1
        el.style.fontSize = `${size}px`
      }
      setFontSize(size)
    }
    fit()
    // Fitting changes the element's height, so react to width changes only —
    // refitting on our own mutations would loop the observer.
    let lastWidth = el.clientWidth
    const observer = new ResizeObserver(() => {
      if (el.clientWidth === lastWidth) return
      lastWidth = el.clientWidth
      fit()
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [maxFontSize, text])

  return { fontSize, ref }
}
