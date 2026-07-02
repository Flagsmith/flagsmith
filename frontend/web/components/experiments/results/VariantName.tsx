import { FC } from 'react'
import ColorSwatch from 'components/ColorSwatch'

type VariantNameProps = {
  name: string
  colour: string
}

const VariantName: FC<VariantNameProps> = ({ colour, name }) => (
  <span>
    <ColorSwatch
      color={colour}
      shape='circle'
      size='sm'
      className='me-1 align-middle'
    />
    <strong>{name}</strong>
  </span>
)

export default VariantName
