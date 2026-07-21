import React, { useEffect, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import ScaleRow from './components/ScaleRow'
import type { Scale } from './components/ScaleRow'

// @ts-expect-error raw-loader import
import primitivesSource from '!!raw-loader!../web/styles/_primitives.scss'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Palette',
}
export default meta

// ---------------------------------------------------------------------------
// Parse _primitives.scss at build time
// ---------------------------------------------------------------------------

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
// Story
// ---------------------------------------------------------------------------

const PalettePage: React.FC = () => {
  const [scales, setScales] = useState<Scale[]>([])

  useEffect(() => {
    setScales(parsePrimitives(primitivesSource))
  }, [])

  return (
    <DocPage
      title='Primitive Colour Palette'
      description={
        <>
          Auto-generated from <code>web/styles/_primitives.scss</code>. Add a
          new variable to the SCSS file and it will appear here automatically.
        </>
      }
    >
      {scales.map((scale) => (
        <ScaleRow key={scale.name} scale={scale} />
      ))}
    </DocPage>
  )
}

export const Primitives: StoryObj = {
  render: () => <PalettePage />,
}
