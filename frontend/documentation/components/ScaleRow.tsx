import React from 'react'

type Swatch = { step: string; hex: string; variable: string }
type Scale = { name: string; swatches: Swatch[] }

const SwatchCard: React.FC<{ swatch: Swatch }> = ({ swatch }) => {
  const r = parseInt(swatch.hex.slice(1, 3), 16)
  const g = parseInt(swatch.hex.slice(3, 5), 16)
  const b = parseInt(swatch.hex.slice(5, 7), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  const textColor = luminance > 0.5 ? '#1a2634' : '#ffffff'

  return (
    <div className='swatch-card'>
      <div
        className='swatch-card__colour'
        style={{ background: swatch.hex, color: textColor }}
      >
        {swatch.step}
      </div>
      <code className='swatch-card__hex'>{swatch.hex}</code>
    </div>
  )
}

const ScaleRow: React.FC<{ scale: Scale }> = ({ scale }) => (
  <div className='scale-row'>
    <h3 className='scale-row__title'>{scale.name}</h3>
    <div className='scale-row__swatches'>
      {scale.swatches.map((s) => (
        <SwatchCard key={s.variable} swatch={s} />
      ))}
    </div>
  </div>
)

export default ScaleRow
export type { Scale, Swatch }
