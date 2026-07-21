import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import DocPage from './components/DocPage'
import Swatch from './components/Swatch'

// ---------------------------------------------------------------------------
// Colour data — inlined to avoid importing Constants (which pulls in the
// full app dependency tree and breaks Storybook's ESM context).
// Source of truth: common/constants.ts
// ---------------------------------------------------------------------------

const TAG_COLOURS = [
  { hex: '#3d4db6', name: 'Indigo' },
  { hex: '#ea5a45', name: 'Coral' },
  { hex: '#c6b215', name: 'Gold' },
  { hex: '#60bd4e', name: 'Green' },
  { hex: '#fe5505', name: 'Orange' },
  { hex: '#1492f4', name: 'Blue' },
  { hex: '#14c0f4', name: 'Cyan' },
  { hex: '#c277e0', name: 'Lavender' },
  { hex: '#039587', name: 'Teal' },
  { hex: '#344562', name: 'Navy' },
  { hex: '#ffa500', name: 'Amber' },
  { hex: '#3cb371', name: 'Mint' },
  { hex: '#d3d3d3', name: 'Silver' },
  { hex: '#5D6D7E', name: 'Slate' },
  { hex: '#641E16', name: 'Maroon' },
  { hex: '#5B2C6F', name: 'Plum' },
  { hex: '#D35400', name: 'Burnt Orange' },
  { hex: '#F08080', name: 'Salmon' },
  { hex: '#AAC200', name: 'Lime' },
  { hex: '#DE3163', name: 'Cerise' },
]

const DEFAULT_TAG_COLOUR = '#dedede'

const PROJECT_COLOURS = [
  '#906AF6',
  '#FAE392',
  '#42D0EB',
  '#56CCAD',
  '#FFBE71',
  '#F57C78',
]

const FEATURE_HEALTH = {
  healthyColor: '#60bd4e',
  unhealthyColor: '#D35400',
}

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },
  title: 'Design System/Tag & Project Colours',
}
export default meta

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const TagColours: StoryObj = {
  name: 'Tag colours',
  render: () => (
    <DocPage
      title='Tag colours'
      description={
        <>
          20 decorative colours users pick from when creating tags. Will be
          defined in <code>_categorical.scss</code> as CSS custom properties (
          <code>--color-tag-1</code> through <code>--color-tag-20</code>).
          Currently in <code>constants.ts</code> pending migration. These are
          NOT semantic tokens &mdash; they are categorical identifiers that need
          to be visually distinct from each other.
        </>
      }
    >
      <div className='cat-grid'>
        {TAG_COLOURS.map(({ hex, name }) => (
          <Swatch key={hex} colour={hex} label={`${name}\n${hex}`} />
        ))}
      </div>
      <p className='cat-note'>
        Default tag colour: <code>{DEFAULT_TAG_COLOUR}</code>
      </p>
    </DocPage>
  ),
}

export const ProjectColours: StoryObj = {
  name: 'Project colours',
  render: () => (
    <DocPage
      title='Project colours'
      description={
        <>
          6 colours assigned by index for project avatar badges. Will be defined
          in <code>_categorical.scss</code> as <code>--color-project-1</code>{' '}
          through <code>--color-project-6</code>. Currently in{' '}
          <code>constants.ts</code> pending migration. Decorative &mdash; not
          tied to any UI role or theme.
        </>
      }
    >
      <div className='cat-grid'>
        {PROJECT_COLOURS.map((colour: string, i: number) => (
          <Swatch key={colour} colour={colour} label={`[${i}] ${colour}`} />
        ))}
      </div>
    </DocPage>
  ),
}

export const FeatureHealthColours: StoryObj = {
  name: 'Feature health colours',
  render: () => (
    <DocPage
      title='Feature health colours'
      description={
        <>
          Status colours for feature health indicators. Currently hardcoded in{' '}
          <code>common/constants.ts</code> as{' '}
          <code>Constants.featureHealth</code>. These should migrate to semantic
          feedback tokens: <code>var(--color-success-default)</code> and{' '}
          <code>var(--color-warning-default)</code>.
        </>
      }
    >
      <div className='cat-health-row'>
        <div className='cat-health-item'>
          <Swatch colour={FEATURE_HEALTH.healthyColor} size={32} />
          <div>
            <strong>Healthy</strong>
            <div className='cat-health-item__migration'>
              Should use <code>var(--color-success-default)</code>
            </div>
          </div>
        </div>
        <div className='cat-health-item'>
          <Swatch colour={FEATURE_HEALTH.unhealthyColor} size={32} />
          <div>
            <strong>Unhealthy</strong>
            <div className='cat-health-item__migration'>
              Should use <code>var(--color-warning-default)</code>
            </div>
          </div>
        </div>
      </div>
    </DocPage>
  ),
}
