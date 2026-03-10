import React, { useEffect, useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react-webpack5'

// @ts-expect-error raw-loader import
import primitivesSource from '!!raw-loader!../web/styles/_primitives.scss'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Colour Palette',
}
export default meta

// ---------------------------------------------------------------------------
// Parse _primitives.scss at build time
// ---------------------------------------------------------------------------

type Swatch = { step: string; hex: string; variable: string }
type Scale = { name: string; swatches: Swatch[] }

function parsePrimitives(source: string): Scale[] {
  const scales: Scale[] = []
  let current: Scale | null = null

  for (const line of source.split('\n')) {
    // Section comment: "// Slate (neutrals)" → name = "Slate"
    const sectionMatch = line.match(/^\/\/\s+(\w+)\s+\(/)
    if (sectionMatch) {
      current = { name: sectionMatch[1], swatches: [] }
      scales.push(current)
      continue
    }

    // Variable: "$slate-50:  #fafafb;" → step=50, hex=#fafafb
    const varMatch = line.match(/^\$(\w+)-(\d+):\s*(#[0-9a-fA-F]{6});/)
    if (varMatch && current) {
      current.swatches.push({
        hex: varMatch[3],
        step: varMatch[2],
        variable: `$${varMatch[1]}-${varMatch[2]}`,
      })
    }
  }

  return scales
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

const SwatchCard: React.FC<{ swatch: Swatch }> = ({ swatch }) => {
  const r = parseInt(swatch.hex.slice(1, 3), 16)
  const g = parseInt(swatch.hex.slice(3, 5), 16)
  const b = parseInt(swatch.hex.slice(5, 7), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  const textColor = luminance > 0.5 ? '#1a2634' : '#ffffff'

  return (
    <div
      style={{
        display: 'flex',
        flex: 1,
        flexDirection: 'column',
        gap: 4,
        minWidth: 0,
      }}
    >
      <div
        style={{
          alignItems: 'flex-end',
          background: swatch.hex,
          border: '1px solid rgba(128,128,128,0.2)',
          borderRadius: 8,
          color: textColor,
          display: 'flex',
          fontSize: 11,
          fontWeight: 600,
          height: 56,
          padding: 6,
        }}
      >
        {swatch.step}
      </div>
      <code
        style={{ color: 'var(--color-text-secondary, #656d7b)', fontSize: 10 }}
      >
        {swatch.hex}
      </code>
    </div>
  )
}

const ScaleRow: React.FC<{ scale: Scale }> = ({ scale }) => (
  <div style={{ marginBottom: 32 }}>
    <h3
      style={{
        color: 'var(--color-text-default, #1a2634)',
        fontSize: 16,
        fontWeight: 700,
        marginBottom: 12,
      }}
    >
      {scale.name}
    </h3>
    <div style={{ display: 'flex', gap: 6 }}>
      {scale.swatches.map((s) => (
        <SwatchCard key={s.variable} swatch={s} />
      ))}
    </div>
  </div>
)

// ---------------------------------------------------------------------------
// Story
// ---------------------------------------------------------------------------

const PalettePage: React.FC = () => {
  const [scales, setScales] = useState<Scale[]>([])

  useEffect(() => {
    setScales(parsePrimitives(primitivesSource))
  }, [])

  return (
    <div style={{ fontFamily: "'OpenSans', sans-serif", maxWidth: 960 }}>
      <h2
        style={{ color: 'var(--color-text-default, #1a2634)', marginBottom: 4 }}
      >
        Primitive Colour Palette
      </h2>
      <p
        style={{
          color: 'var(--color-text-secondary, #656d7b)',
          fontSize: 14,
          marginBottom: 24,
        }}
      >
        Auto-generated from{' '}
        <code style={{ color: 'inherit' }}>web/styles/_primitives.scss</code>.
        Add a new variable to the SCSS file and it will appear here
        automatically.
      </p>
      {scales.map((scale) => (
        <ScaleRow key={scale.name} scale={scale} />
      ))}
    </div>
  )
}

export const Primitives: StoryObj = {
  render: () => <PalettePage />,
}
