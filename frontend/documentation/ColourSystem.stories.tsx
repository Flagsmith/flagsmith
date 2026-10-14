import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import ScaleRow from './components/ScaleRow'
import type { Scale, Swatch } from './components/ScaleRow'
import tokens from 'common/theme/tokens.json'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Design System/Colour System',
}
export default meta

type Entry = { cssVar: string; dark: string; light: string }

// The JSON import types each group by its exact keys; read them by name.
const groups = tokens as unknown as Record<string, Record<string, Entry>>

const group = (name: string): Record<string, Entry> => groups[name] ?? {}

const toSwatch = ([step, entry]: [string, Entry]): Swatch => ({
  dark: entry.dark,
  hex: entry.light,
  step,
  variable: entry.cssVar,
})

const byStep = (a: Swatch, b: Swatch) => Number(a.step) - Number(b.step)

const ramp = (name: string): Scale => ({
  name: name[0].toUpperCase() + name.slice(1),
  swatches: Object.entries(group(name)).map(toSwatch).sort(byStep),
})

/** The state group is flat (`danger-500`); the design system shows it by hue. */
const stateHue = (hue: string, name: string): Scale => ({
  compact: true,
  name,
  swatches: Object.entries(group('state'))
    .filter(([key]) => key.startsWith(`${hue}-`))
    .map(toSwatch)
    .map((swatch) => ({ ...swatch, step: swatch.step.split('-')[1] }))
    .sort(byStep),
})

const surfaces = tokens.color.surface as Record<string, Entry>

const surface: Scale = {
  compact: true,
  name: 'Surface',
  swatches: [
    ...['default', 'subtle', 'muted', 'emphasis']
      .filter((key) => surfaces[key])
      .map((key) => toSwatch([key, surfaces[key]])),
    ...Object.entries(group('always')).map(([key, entry]) =>
      toSwatch([`always-${key}`, entry]),
    ),
  ],
}

const scales: Scale[] = [
  ramp('primary'),
  ramp('neutral'),
  surface,
  stateHue('info', 'Informational'),
  stateHue('success', 'Success'),
  stateHue('warning', 'Warning'),
  stateHue('danger', 'Danger'),
]

const ColourSystemPage: React.FC = () => (
  <DocPage title='Colour System'>
    {scales.map((scale) => (
      <ScaleRow key={scale.name} scale={scale} />
    ))}
  </DocPage>
)

export const ColourSystem: StoryObj = {
  name: 'Colour system',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => <ColourSystemPage />,
}
