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

const primitives = tokens.primitives as Record<string, string>

const group = (name: string): Record<string, Entry> =>
  (tokens as unknown as Record<string, Record<string, Entry>>)[name] ?? {}

/** Resolve a stored value that may name a primitive rather than hold a hex. */
const hex = (value: string) => primitives[value] ?? value

const toSwatch = ([step, entry]: [string, Entry]): Swatch => ({
  dark: hex(entry.dark),
  hex: hex(entry.light),
  step,
  variable: entry.cssVar,
})

const byStep = (a: Swatch, b: Swatch) => Number(a.step) - Number(b.step)

const ramp = (name: string, description: string): Scale => ({
  description,
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

const surfaces = tokens.color.surface as unknown as Record<string, Entry>

const surface: Scale = {
  compact: true,
  description:
    'The grounds a page is built on, plus the two colours that stay put whatever the theme.',
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

const content: Scale = {
  compact: true,
  description:
    'Decorative identifiers, most often a tag category. The same on both themes: pale enough to carry dark text and to separate from either page.',
  name: 'Content',
  swatches: Object.keys(primitives)
    .filter(
      (name) => name.startsWith('content-') && name !== 'content-always-dark',
    )
    .map((name) => ({
      hex: primitives[name],
      step: name.replace('content-', ''),
      variable: `--${name}`,
    })),
}

const scales: Scale[] = [
  ramp(
    'primary',
    'Purple is the primary colour: primary actions, buttons, text links.',
  ),
  ramp(
    'neutral',
    'Structure and clarity. Layout, text and UI elements that support the content rather than compete with it.',
  ),
  surface,
  stateHue('info', 'Informational'),
  stateHue('success', 'Success'),
  stateHue('warning', 'Warning'),
  stateHue('danger', 'Danger'),
  ...(content.swatches.length ? [content] : []),
]

const ColourSystemPage: React.FC = () => (
  <DocPage
    title='Colour System'
    description={
      <>
        The design system&rsquo;s own ramps, read from{' '}
        <code>common/theme/tokens.json</code>, so this page cannot drift from
        what ships. Swatches show the light value; where a token differs between
        themes the dark value follows it, and several of these ramps invert.
      </>
    }
  >
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
