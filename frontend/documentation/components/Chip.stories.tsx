import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip from 'components/base/Chip'
import Icon, { IconName } from 'components/icons/Icon'
import { contentColourNames } from 'common/theme/tokens'

const meta: Meta<typeof Chip> = {
  args: { children: 'Production' },
  component: Chip,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'A small labelled pill. Layout comes from Bootstrap utilities and colour from token utilities; padding, sizes, border and truncation are in SCSS. Icons go in as children. `none` leaves the colour to the caller, for a colour a user picked rather than a semantic role.',
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

// How Tag composes Chip: a decorative colour a user picked is not a semantic
// variant, so it arrives on `colour`. System tags take neither, and carry
// their state in the icon instead.
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
        <Chip key={label} size='xs' variant='outline'>
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
      {contentColourNames.map((colour) => (
        <Chip colour={colour} key={colour} size='xs'>
          Custom
        </Chip>
      ))}
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip size='md'>Medium</Chip>
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
