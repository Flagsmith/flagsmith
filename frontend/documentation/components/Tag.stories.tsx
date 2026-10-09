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
          'A project tag. The chip is the neutral one in both themes and the colour is a dot, so the label is always text-default and the colour never has to be legible for the tag to be. The dot is the hex stored on the tag, drawn as it is.',
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

export const Default: Story = { args: { tag: tag({}) } }

export const EveryColour: Story = {
  name: 'Every colour',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      {Constants.tagColors.map((color: string) => (
        <Tag key={color} tag={tag({ color, label: 'Checkout' })} />
      ))}
    </div>
  ),
}

export const Extremes: Story = {
  name: 'Colours that barely read',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      <Tag tag={tag({ color: '#d3d3d3', label: 'Near white' })} />
      <Tag tag={tag({ color: '#641e16', label: 'Near black' })} />
      <Tag tag={tag({ color: '#ffffff', label: 'White' })} />
      <Tag tag={tag({ color: '#000000', label: 'Black' })} />
    </div>
  ),
}

export const Permanent: Story = {
  args: { tag: tag({ is_permanent: true, label: 'Core' }) },
}

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
  name: 'Selectable, showing the ring',
  render: () => <SelectableTags />,
}
