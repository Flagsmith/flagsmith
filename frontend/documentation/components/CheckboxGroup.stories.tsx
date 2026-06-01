import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import CheckboxGroup from 'components/base/forms/CheckboxGroup'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/CheckboxGroup',
}
export default meta

type Story = StoryObj

const items = [
  { label: 'Read', value: 'read' },
  { label: 'Write', value: 'write' },
  { label: 'Admin', value: 'admin' },
]

const Interactive = () => {
  const [selected, setSelected] = useState<string[]>(['read'])
  return (
    <CheckboxGroup
      items={items}
      selectedValues={selected}
      onChange={setSelected}
    />
  )
}

export const Default: Story = {
  render: () => <Interactive />,
}

export const AllSelected: Story = {
  render: () => (
    <CheckboxGroup
      items={items}
      selectedValues={['read', 'write', 'admin']}
      onChange={() => {}}
    />
  ),
}

export const NoneSelected: Story = {
  render: () => (
    <CheckboxGroup items={items} selectedValues={[]} onChange={() => {}} />
  ),
}
