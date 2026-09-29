import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip from 'components/base/Chip'
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
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. `none` leaves the colour to the caller, for a decorative colour a user picked rather than a semantic role. Selection lives in ToggleChip and count badges are a separate Badge concern. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
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

// How Tag composes Chip: a decorative colour a user picked is not a semantic
// variant, so it arrives as a tag-* swatch class in className. System tags take
// none of it, and carry their state in the icon instead.
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
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      {SYSTEM_TAGS.map(({ icon, label }) => (
        <Chip
          className='bg-surface-default border-default text-default'
          key={label}
          size='sm'
          variant='none'
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
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      {Constants.tagColors.map((colour: string) => (
        <Chip
          className={getTagSwatchUtilities(colour)}
          key={colour}
          size='sm'
          variant='none'
        >
          Custom
        </Chip>
      ))}
    </div>
  ),
}
