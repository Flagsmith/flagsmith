import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import InputField from 'components/base/forms/InputField'

const meta: Meta<typeof InputField> = {
  component: InputField,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/InputField',
}
export default meta

type Story = StoryObj<typeof InputField>

const Interactive = () => {
  const [value, setValue] = useState('')
  return (
    <InputField
      label='Email'
      placeholder='you@example.com'
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  )
}

export const Default: Story = {
  render: () => <Interactive />,
}

export const Required: Story = {
  render: () => (
    <InputField label='Email' required placeholder='you@example.com' />
  ),
}

export const WithError: Story = {
  render: () => (
    <InputField
      label='Email'
      value='not-an-email'
      error='Enter a valid email address.'
    />
  ),
}

export const Disabled: Story = {
  render: () => <InputField label='Email' disabled value='you@example.com' />,
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <InputField label='Default' placeholder='Default' />
      <InputField label='Small' size='small' placeholder='Small' />
      <InputField label='Extra small' size='xSmall' placeholder='Extra small' />
    </div>
  ),
}
