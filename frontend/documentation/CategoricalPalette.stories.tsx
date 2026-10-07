import React, { FC } from 'react'
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

// The light theme fills. A tag carries its own surface rather than following
// the page, and in dark the fill and the ink swap roles.
// Both halves of every tag, per theme: a fill is only legible next to the ink
// it ships with, so the page shows the pair rather than the fill alone.
const TAG_PAIRINGS = Object.entries(tokens.content).map(([name, fill]) => {
  const ink = tokens.contentInk[name as keyof typeof tokens.contentInk]
  return {
    dark: { fill: fill.dark, ink: ink.dark },
    light: { fill: fill.light, ink: ink.light },
    name,
  }
})

type TagPreviewProps = { fill: string; ink: string; name: string }

// The only place a tag is drawn from values rather than its utility class: the
// page shows both themes at once, so neither can come from the ambient one.
const TagPreview: FC<TagPreviewProps> = ({ fill, ink, name }) => (
  <span className='cat-tag' style={{ backgroundColor: fill, color: ink }}>
    {name}
  </span>
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
          that made contrast a function of the user&rsquo;s chosen hue. These
          are the design system&rsquo;s Content colours, shown here on light,
          where the shared ink below is the label. Dark swaps the two: the fill
          becomes the ink and a deep version of the same hue becomes the fill.
          Both pairings clear AA ({AA_NORMAL_TEXT}:1), enforced by{' '}
          <code>tagSwatches.test.ts</code>.
        </>
      }
    >
      {(['light', 'dark'] as const).map((theme) => (
        <div key={theme}>
          <h3 className='cat-note'>{theme}</h3>
          <div className='d-flex flex-wrap gap-3'>
            {TAG_PAIRINGS.map(({ name, ...pairing }) => {
              const { fill, ink } = pairing[theme]
              return (
                <div
                  className='d-flex flex-column align-items-center gap-1'
                  key={name}
                >
                  <TagPreview fill={fill} ink={ink} name={name} />
                  <small className='text-secondary'>
                    {contrastRatio(fill, ink).toFixed(2)}:1
                  </small>
                </div>
              )
            })}
          </div>
        </div>
      ))}
      <p className='cat-note'>
        System tags (Issue, PR, Stale, Unhealthy) are not on this scale. They
        take no fill at all: <code>border-default</code> and{' '}
        <code>text-default</code> plus a coloured icon, so the state is carried
        by the icon and the border rather than the fill.
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
