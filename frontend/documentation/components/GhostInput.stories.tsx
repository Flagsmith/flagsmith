import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import GhostInput from 'components/base/forms/GhostInput'

const meta: Meta = {
  parameters: { layout: 'centered' },
  title: 'Components/Forms/GhostInput',
}
export default meta

type Story = StoryObj

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
