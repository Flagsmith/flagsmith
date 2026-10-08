import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import Chip from 'components/base/Chip'
import DocPage from './components/DocPage'
import Swatch from './components/Swatch'
import tokens from 'common/theme/tokens.json'
import { contentColourNames, contentColours } from 'common/theme/tokens'
import { contrastRatio } from 'common/theme/contrast'

// ---------------------------------------------------------------------------
// Colour data — inlined to avoid importing Constants (which pulls in the
// full app dependency tree and breaks Storybook's ESM context).
// Source of truth: common/constants.ts. The tag scale is not copied here; it
// comes from tokens.json below, so it cannot drift.
// ---------------------------------------------------------------------------

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

// A tag is a neutral chip in both themes and the hue is an 8px dot, so one
// value per hue serves both. The chip it sits on is what it has to read on.
const CHIP = tokens.color.surface.subtle
const TAG_DOTS = contentColourNames.map(
  (name) => [name, contentColours[name]] as const,
)

export const TagSwatches: StoryObj = {
  name: 'Tag swatches',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <DocPage
      title='Tag swatches'
      description={
        <>
          The scale a custom tag picks from, replacing the runtime colour maths
          that made contrast a function of the user&rsquo;s chosen hue. The chip
          is the neutral one in both themes and the hue is the dot, so the label
          is always <code>text-default</code> and no pairing of fill and ink has
          to be checked. One value per hue serves both themes: each clears 3:1
          on the light chip and on the dark one, enforced by{' '}
          <code>tagSwatches.test.ts</code>. The numbers below are the light
          chip; the dark figure is alongside.
        </>
      }
    >
      <div className='d-flex flex-wrap gap-3'>
        {TAG_DOTS.map(([name, hex]) => (
          <div
            className='d-flex flex-column align-items-center gap-1'
            key={name}
          >
            <Chip dot={name} size='xs'>
              {name}
            </Chip>
            <small className='text-secondary'>
              {contrastRatio(hex, CHIP.light).toFixed(2)} /{' '}
              {contrastRatio(hex, CHIP.dark).toFixed(2)}
            </small>
          </div>
        ))}
      </div>
      <p className='cat-note'>
        System tags (Issue, PR, Stale, Unhealthy) take no dot. Their state is in
        a coloured icon in the same slot, so the two kinds of tag are the same
        chip with a different thing in front of the label.
      </p>
      <div className='d-flex mt-3'>
        <Chip size='xs' variant='outline'>
          System tag
        </Chip>
      </div>
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
