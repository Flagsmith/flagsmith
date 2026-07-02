import { FC } from 'react'

type VariantNameProps = {
  name: string
  colour: string
}

const VariantName: FC<VariantNameProps> = ({ colour, name }) => (
  <span>
    <span
      className='d-inline-block rounded-circle'
      style={{
        backgroundColor: colour,
        height: 8,
        marginRight: 3,
        verticalAlign: 'middle',
        width: 8,
      }}
    />
    <strong>{name}</strong>
  </span>
)

export default VariantName
