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
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. `variant` covers neutral, accent and the four status colours; `pill` gives the fully rounded ends that status and count badges use, and `ChipDot` adds the leading dot in `currentColor`. Selection lives in ToggleChip. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
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

export const StatusVariants: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip variant='info' size='sm' pill>
        <ChipDot />
        Draft
      </Chip>
      <Chip variant='success' size='sm' pill>
        <ChipDot />
        Running
      </Chip>
      <Chip variant='warning' size='sm' pill>
        <ChipDot />
        Paused
      </Chip>
      <Chip variant='muted' size='sm' pill>
        <ChipDot />
        Completed
      </Chip>
    </div>
  ),
}

export const Counts: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip variant='accent' size='xs' pill>
        5
      </Chip>
      <Chip variant='neutral' size='xs' pill>
        0
      </Chip>
      <Chip variant='neutral' size='xs' pill>
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
