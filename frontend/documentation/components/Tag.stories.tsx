import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Tag from 'components/tags/Tag'
import Constants from 'common/constants'
import type { Tag as TTag } from 'common/types/responses'

const meta: Meta<typeof Tag> = {
  component: Tag,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'A project tag. Custom tags take a fill from the design system Content palette, keyed on the colour stored on the tag so nothing needs migrating. System tags (Stale, GitHub, GitLab, Unhealthy) stay on the default surface and carry their state in a coloured icon rather than the fill, so the state survives for anyone who cannot tell the fills apart.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Data Display/Tag',
}
export default meta

type Story = StoryObj<typeof Tag>

const tag = (over: Partial<TTag>): Partial<TTag> => ({
  color: Constants.tagColors[0],
  label: 'Checkout',
  type: 'NONE',
  ...over,
})

export const Custom: Story = { args: { tag: tag({}) } }

export const EveryColour: Story = {
  name: 'Every colour',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      {Constants.tagColors.map((colour: string) => (
        <Tag key={colour} tag={tag({ color: colour, label: 'Checkout' })} />
      ))}
    </div>
  ),
}

export const SystemTags: Story = {
  name: 'System tags',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      {(['STALE', 'GITHUB', 'GITLAB', 'UNHEALTHY'] as const).map((type) => (
        <Tag key={type} tag={tag({ label: type, type })} />
      ))}
    </div>
  ),
}

// A colour the picker never offered: the API takes any hex, so a tag created
// outside the UI falls through to the neutral rather than an unvalidated fill.
export const UnknownColour: Story = {
  args: { tag: tag({ color: '#123456', label: 'Set via API' }) },
  name: 'Colour outside the scale',
}

export const AsADot: Story = {
  args: { isDot: true, tag: tag({}) },
  name: 'As a dot',
}

/** Hooks cannot live in a story's render, so selection state gets a component. */
const SelectableTags: React.FC = () => {
  const [picked, setPicked] = useState<string>('Checkout')
  return (
    <div className='d-flex flex-wrap gap-1'>
      {['Checkout', 'Billing', 'Search'].map((label, i) => (
        <Tag
          key={label}
          onClick={() => setPicked(label)}
          selected={picked === label}
          tag={tag({ color: Constants.tagColors[i], label })}
        />
      ))}
    </div>
  )
}

export const Selectable: Story = {
  render: () => <SelectableTags />,
}
