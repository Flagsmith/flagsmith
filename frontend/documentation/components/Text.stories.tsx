import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Text, {
  BodyVariant,
  HeadingLevel,
  HeadingVariant,
  TextWeight,
} from 'components/base/Text'

const meta: Meta = {
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'Typography primitive. `variant` picks the step on the type scale, `level` says where a heading sits in the document outline. The two are independent, so text can look like an h5 while still being the section heading. Colour is not a prop: use the `text-*` token utilities.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Base/Text',
}
export default meta

type Story = StoryObj

const HEADINGS: HeadingVariant[] = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
const BODY: BodyVariant[] = ['b1', 'b2', 'b3', 'b4']
const WEIGHTS: TextWeight[] = ['regular', 'medium', 'semibold', 'bold']

export const Headings: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      {HEADINGS.map((variant, i) => (
        <Text key={variant} variant={variant} level={(i + 1) as HeadingLevel}>
          {variant.toUpperCase()} Manage your feature flags
        </Text>
      ))}
    </div>
  ),
}

export const Body: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      {BODY.map((variant) => (
        <Text key={variant} variant={variant} as='p' className='mb-0'>
          {variant.toUpperCase()} Your plan renews on 1 August 2026.
        </Text>
      ))}
    </div>
  ),
}

export const Weights: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      {WEIGHTS.map((weight) => (
        <Text key={weight} variant='b1' as='p' weight={weight} className='mb-0'>
          {weight} — overrides the weight the variant carries
        </Text>
      ))}
    </div>
  ),
}

// The reason this is a component and not a set of classes: an h5-sized heading
// that is really the second level of the page.
export const LevelIsSeparateFromSize: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <Text variant='h4' level={1}>
        Usage
      </Text>
      <Text variant='h5' level={2}>
        Change History
      </Text>
      <Text variant='h6' level={3}>
        Segment overrides
      </Text>
      <Text variant='b3' as='p' className='text-secondary mb-0'>
        Rendered as h1, h2 and h3 despite being sized h4, h5 and h6.
      </Text>
    </div>
  ),
}

export const WithColourUtilities: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Text variant='b1' as='p' className='mb-0'>
        Default body colour
      </Text>
      <Text variant='b1' as='p' className='text-secondary mb-0'>
        text-secondary
      </Text>
      <Text variant='b1' as='p' className='text-danger mb-0'>
        text-danger
      </Text>
      <Text variant='b1' as='p' className='text-success mb-0'>
        text-success
      </Text>
    </div>
  ),
}
