import { FC } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import useFitText from 'common/hooks/useFitText'
import './results.scss'

type VariantNameProps = {
  name: string
  colour: string
  fontSize?: number
  fit?: boolean
}

// fit shrinks the font until the name matches the container width, with an
// ellipsis floor; it renders as a block, which drops the prose baseline
// alignment — leave it off inside a sentence.
const VariantName: FC<VariantNameProps> = ({ colour, fit, fontSize, name }) => {
  const large = !!fontSize && fontSize >= 20
  const { fontSize: fittedSize, ref } = useFitText<HTMLSpanElement>(
    fit ? fontSize : undefined,
    name,
  )
  const appliedSize = fit ? fittedSize : fontSize

  return (
    <span
      className={fit ? 'variant-name--fit' : undefined}
      ref={ref}
      style={appliedSize ? { fontSize: appliedSize } : undefined}
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
