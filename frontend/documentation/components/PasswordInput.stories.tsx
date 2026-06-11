import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import PasswordInput from 'components/base/forms/PasswordInput'

const meta: Meta<typeof PasswordInput> = {
  component: PasswordInput,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/PasswordInput',
}
export default meta

type Story = StoryObj<typeof PasswordInput>

const Interactive = () => {
  const [value, setValue] = useState('hunter2')
  return (
    <PasswordInput
      placeholder='Password'
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  )
}

export const Default: Story = {
  render: () => <Interactive />,
}

export const Disabled: Story = {
  render: () => <PasswordInput value='hunter2' disabled />,
}
