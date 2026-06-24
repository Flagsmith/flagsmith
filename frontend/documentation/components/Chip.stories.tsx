import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip from 'components/base/Chip'

const meta: Meta<typeof Chip> = {
  args: { children: 'Production' },
  component: Chip,
  parameters: {
    docs: {
      description: {
        component:
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. Selection lives in ToggleChip and count badges are a separate Badge concern. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/Chip',
}
export default meta

type Story = StoryObj<typeof Chip>

export const Neutral: Story = {}

export const Accent: Story = {
  args: { children: '"hello"', variant: 'accent' },
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip size='default'>Default</Chip>
      <Chip size='sm'>Small</Chip>
      <Chip size='xs'>Extra small</Chip>
    </div>
  ),
}

export const Removable: Story = {
  args: { children: 'feature-flag', onRemove: () => undefined },
}

export const Truncated: Story = {
  args: {
    children: '{ "test": "testvalue-that-keeps-going-and-going" }',
    truncate: true,
    variant: 'accent',
  },
}

export const Group: Story = {
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      <Chip>Development</Chip>
      <Chip variant='accent'>Staging</Chip>
      <Chip onRemove={() => undefined}>Production</Chip>
    </div>
  ),
}
