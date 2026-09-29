import React from 'react'

// `dark` only where a swatch is themed: primitives hold one value, the design
// system's ramps hold two and often invert between them.
type Swatch = { step: string; hex: string; variable: string; dark?: string }
// `compact` caps the swatch width instead of stretching to fill. A scale of
// three would otherwise take the same room as one of fourteen.
type Scale = {
  name: string
  description?: string
  compact?: boolean
  swatches: Swatch[]
}

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
      <code className='swatch-card__hex'>
        {swatch.hex}
        {swatch.dark && swatch.dark !== swatch.hex && <> · {swatch.dark}</>}
      </code>
    </div>
  )
}

const ScaleRow: React.FC<{ scale: Scale }> = ({ scale }) => (
  <div className='scale-row'>
    <h3 className='scale-row__title'>{scale.name}</h3>
    {scale.description && (
      <p className='scale-row__description'>{scale.description}</p>
    )}
    <div
      className={`scale-row__swatches${
        scale.compact ? ' scale-row__swatches--compact' : ''
      }`}
    >
      {scale.swatches.map((s) => (
        <SwatchCard key={s.variable} swatch={s} />
      ))}
    </div>
  </div>
)

export default ScaleRow
export type { Scale, Swatch }
