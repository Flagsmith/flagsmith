import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip, { ChipDot } from 'components/base/Chip'
import Icon, { IconName } from 'components/icons/Icon'
import Constants from 'common/constants'
import { getTagSwatchUtilities } from 'components/tags/tagSwatch'

const meta: Meta<typeof Chip> = {
  args: { children: 'Production' },
  component: Chip,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. `variant` covers neutral, accent, the five status colours and `solid`; `ChipDot` adds the leading dot in `currentColor`. Radius is a fixed 6px from the tags frame, so there is no shape prop. `selected` renders a leading checkbox with a tick; a chip with no children shows the tick alone, for bare swatches like the tag colour picker. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
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

// How Tag composes Chip: a decorative colour a user picked is not a semantic
// variant, so it arrives as a tag-* swatch class in className. System
// tags take none of it, and carry their state in the icon instead.
const SYSTEM_TAGS: { label: string; icon: IconName }[] = [
  { icon: 'issue-closed', label: 'Issue closed' },
  { icon: 'issue-linked', label: 'Issue open' },
  { icon: 'pr-closed', label: 'PR closed' },
  { icon: 'pr-dequeued', label: 'PR dequeued' },
  { icon: 'pr-draft', label: 'PR draft' },
  { icon: 'stale', label: 'Stale' },
  { icon: 'pr-linked', label: 'PR open' },
  { icon: 'pr-merged', label: 'PR merged' },
]

export const AsSystemTag: Story = {
  name: 'As a system tag',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      {SYSTEM_TAGS.map(({ icon, label }) => (
        <Chip
          className='bg-surface-default border-default text-default'
          key={label}
          size='xs'
        >
          {label}
          <Icon name={icon} />
        </Chip>
      ))}
    </div>
  ),
}

export const AsCustomTag: Story = {
  name: 'As a custom tag',
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      {Constants.tagColors.map((colour: string) => (
        <Chip
          className={`border-0 ${getTagSwatchUtilities(colour)}`}
          key={colour}
          size='xs'
        >
          Custom
        </Chip>
      ))}
    </div>
  ),
}

export const Selected: Story = {
  name: 'Selected',
  render: () => (
    <div className='d-flex flex-wrap gap-2 align-items-center'>
      <Chip selected>Selected</Chip>
      <Chip selected={false}>Not selected</Chip>
      <Chip className='tag-light-green border-0' selected />
      <Chip className='tag-light-green border-0' selected={false} />
    </div>
  ),
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
