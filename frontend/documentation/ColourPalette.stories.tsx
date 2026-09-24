import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import ScaleRow from './components/ScaleRow'
import type { Scale } from './components/ScaleRow'
import tokens from 'common/theme/tokens.json'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Palette',
}
export default meta

const primitives = tokens.primitives as Record<string, string>

/** Group `{ 'slate-50': '#fafafb' }` into scales, ordered by step. */
function buildScales(): Scale[] {
  const byFamily = new Map<string, Scale>()

  for (const name of Object.keys(primitives)) {
    const match = name.match(/^([a-z]+)-(\d+)$/)
    if (!match) continue

    const [, family, step] = match
    const scale = byFamily.get(family) ?? {
      name: family[0].toUpperCase() + family.slice(1),
      swatches: [],
    }
    byFamily.set(family, scale)

    scale.swatches.push({
      hex: primitives[name],
      step,
      variable: `--${name}`,
    })
  }

  for (const scale of byFamily.values()) {
    scale.swatches.sort((a, b) => Number(a.step) - Number(b.step))
  }

  return [...byFamily.values()]
}

const PalettePage: React.FC = () => (
  <DocPage
    title='Primitive Colour Palette'
    description={
      <>
        Generated from <code>common/theme/tokens.json</code>, the same source
        the CSS custom properties are built from, so this page cannot drift from
        what ships.
      </>
    }
  >
    {buildScales().map((scale) => (
      <ScaleRow key={scale.name} scale={scale} />
    ))}
  </DocPage>
)

export const Primitives: StoryObj = {
  render: () => <PalettePage />,
}
