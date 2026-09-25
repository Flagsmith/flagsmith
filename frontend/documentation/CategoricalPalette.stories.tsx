import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import './docs.scss'
import Chip from 'components/base/Chip'
import DocPage from './components/DocPage'
import Swatch from './components/Swatch'
import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

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

const PRIMITIVES = tokens.primitives as Record<string, string>

// The Content palette, fixed rather than theme-aware: a tag chip carries its
// own surface, so it does not follow the page. One ink serves all of them.
const TAG_FILLS = Object.entries(PRIMITIVES)
  .filter(([name]) => name.startsWith('content-'))
  .map(([name, hex]) => [name.replace('content-', ''), hex] as const)
const TAG_INK = PRIMITIVES['slate-600']

export const TagSwatches: StoryObj = {
  name: 'Tag swatches',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <DocPage
      title='Tag swatches'
      description={
        <>
          The scale a custom tag picks from, replacing the runtime colour maths
          that made contrast a function of the user&rsquo;s chosen hue. These
          are the design system&rsquo;s Content colours, fixed in both themes
          because a chip carries its own surface. Every one clears AA (
          {AA_NORMAL_TEXT}:1) against the shared ink, enforced by{' '}
          <code>tagSwatches.test.ts</code>.
        </>
      }
    >
      <div className='d-flex flex-wrap gap-3'>
        {TAG_FILLS.map(([name, hex]) => (
          <div
            className='d-flex flex-column align-items-center gap-1'
            key={name}
          >
            <Chip className={`border-0 tag-${name}`} size='xs'>
              {name}
            </Chip>
            <small className='text-secondary'>
              {contrastRatio(hex, TAG_INK).toFixed(2)}:1
            </small>
          </div>
        ))}
      </div>
      <p className='cat-note'>
        System tags (Issue, PR, Stale, Unhealthy) are not on this scale. They
        stay on existing tokens &mdash; <code>bg-surface-default</code>,{' '}
        <code>border-default</code>, <code>text-default</code> &mdash; plus a
        coloured icon, so the state is carried by the icon rather than the fill.
      </p>
      <div className='d-flex mt-3'>
        <Chip
          className='bg-surface-default border-default text-default'
          size='xs'
        >
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
