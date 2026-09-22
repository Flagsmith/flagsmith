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
          The 20 decorative colours users currently pick from when creating a
          tag, held in <code>constants.ts</code>. Tags derive their fill, border
          and text from these at render time, which is why most of them fail
          WCAG AA. #8465 replaces that with the validated scale below. These are
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

type TagEntry = { cssVar: string; light: string; dark: string }

const TAG_SURFACES = tokens.tag.surface as Record<string, TagEntry>
const TAG_TEXTS = tokens.tag.text as Record<string, TagEntry>
const TAG_HUES = Object.keys(TAG_SURFACES)

export const TagSwatches: StoryObj = {
  name: 'Tag swatches',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <DocPage
      title='Tag swatches'
      description={
        <>
          The scale a custom tag picks from, replacing the runtime colour maths
          that made contrast a function of the user&rsquo;s chosen hue. Each hue
          is a <code>surface</code> and <code>text</code> pair built from the
          primitive ramps, so a ramp change carries through. Ratios below are
          for the current theme; every pair clears AA ({AA_NORMAL_TEXT}:1) in
          both, enforced by <code>tagSwatches.test.ts</code>.
        </>
      }
    >
      <div className='d-flex flex-wrap gap-3'>
        {TAG_HUES.map((hue) => (
          <div
            className='d-flex flex-column align-items-center gap-1'
            key={hue}
          >
            <Chip className={`border-0 tag-${hue}`} size='xs'>
              {hue}
            </Chip>
            <small className='text-secondary'>
              {contrastRatio(
                TAG_SURFACES[hue].light,
                TAG_TEXTS[hue].light,
              ).toFixed(2)}
              :1 light &middot;{' '}
              {contrastRatio(
                TAG_SURFACES[hue].dark,
                TAG_TEXTS[hue].dark,
              ).toFixed(2)}
              :1 dark
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
