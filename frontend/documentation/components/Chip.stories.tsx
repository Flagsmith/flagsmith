import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip, { ChipDot } from 'components/base/Chip'

const meta: Meta<typeof Chip> = {
  args: { children: 'Production' },
  component: Chip,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. `variant` covers neutral, accent, the five status colours and `solid`; `ChipDot` adds the leading dot in `currentColor`. Radius is a fixed 6px from the tags frame, so there is no shape prop. Selection lives in ToggleChip. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
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

export const Solid: Story = {
  args: { children: 'Enterprise', variant: 'solid' },
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

export const StatusVariants: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip variant='info' size='sm'>
        <ChipDot />
        Draft
      </Chip>
      <Chip variant='success' size='sm'>
        <ChipDot />
        Running
      </Chip>
      <Chip variant='warning' size='sm'>
        <ChipDot />
        Paused
      </Chip>
      <Chip variant='danger' size='sm'>
        <ChipDot />
        Failed
      </Chip>
      <Chip variant='muted' size='sm'>
        <ChipDot />
        Completed
      </Chip>
    </div>
  ),
}

export const Counts: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip variant='accent' size='xs'>
        5
      </Chip>
      <Chip variant='neutral' size='xs'>
        0
      </Chip>
      <Chip variant='neutral' size='xs'>
        128
      </Chip>
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
