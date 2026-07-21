import React from 'react'

type SwatchProps = {
  colour: string
  label?: string
  size?: number
}

const Swatch: React.FC<SwatchProps> = ({ colour, label, size = 40 }) => (
  <div className='cat-swatch'>
    <div
      className='cat-swatch__colour'
      style={{ background: colour, height: size, width: size }}
      title={colour}
    />
    <code className='cat-swatch__label'>{label || colour}</code>
  </div>
)

export default Swatch
export type { SwatchProps }
