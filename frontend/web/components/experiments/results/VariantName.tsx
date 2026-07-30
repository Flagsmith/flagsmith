import { FC, useLayoutEffect, useRef } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import './results.scss'

const FIT_MIN_FONT_SIZE = 14

type VariantNameProps = {
  name: string
  colour: string
  fontSize?: number
  fit?: boolean
}

// fit shrinks the font (down to FIT_MIN_FONT_SIZE, then ellipsis) until the
// name matches the container width; it renders as a block, which drops the
// prose baseline alignment — leave it off inside a sentence.
const VariantName: FC<VariantNameProps> = ({ colour, fit, fontSize, name }) => {
  const large = !!fontSize && fontSize >= 20
  const ref = useRef<HTMLSpanElement>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !fit || !fontSize) return
    const fitText = () => {
      let size = fontSize
      el.style.fontSize = `${size}px`
      while (size > FIT_MIN_FONT_SIZE && el.scrollWidth > el.clientWidth) {
        size -= 1
        el.style.fontSize = `${size}px`
      }
    }
    fitText()
    const observer = new ResizeObserver(fitText)
    observer.observe(el)
    return () => observer.disconnect()
  }, [fit, fontSize, name])

  return (
    <span
      className={fit ? 'variant-name--fit' : undefined}
      ref={ref}
      // In fit mode the layout effect owns fontSize; setting it here too
      // would clobber the fitted size on every re-render.
      style={!fit && fontSize ? { fontSize } : undefined}
      title={fit ? name : undefined}
    >
      <ColorSwatch
        className={`variant-name__swatch${
          large ? ' me-2 variant-name__swatch--lg' : ' me-1'
        }`}
        color={colour}
        shape='circle'
        size={large ? 'md' : 'sm'}
      />
      <strong>{name}</strong>
    </span>
  )
}

export default VariantName
