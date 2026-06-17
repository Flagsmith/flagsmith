import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import GhostInput from 'components/base/forms/GhostInput'

const meta: Meta<typeof GhostInput> = {
  component: GhostInput,
  parameters: { layout: 'centered' },
  title: 'Components/Forms/GhostInput',
}
export default meta

type Story = StoryObj<typeof GhostInput>

const Interactive = () => {
  const [value, setValue] = useState('my-feature-flag')
  return (
    <GhostInput
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder='Type here...'
    />
  )
}

export const Default: Story = {
  render: () => <Interactive />,
}

export const Empty: Story = {
  render: () => (
    <GhostInput value='' onChange={() => {}} placeholder='Enter a name...' />
  ),
}

// Guards the clipping regression: the whole value must render, not "show_demo_butto".
export const LongValue: Story = {
  render: () => (
    <GhostInput
      value='show_demo_button'
      onChange={() => {}}
      placeholder='Enter a name...'
    />
  ),
}
