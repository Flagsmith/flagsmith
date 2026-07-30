import { FC } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import './results.scss'

type VariantNameProps = {
  name: string
  colour: string
  fontSize?: number
}

const VariantName: FC<VariantNameProps> = ({ colour, fontSize, name }) => {
  const large = !!fontSize && fontSize >= 20
  return (
    <span style={fontSize ? { fontSize } : undefined}>
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
