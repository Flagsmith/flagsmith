import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import TextAreaField from 'components/base/forms/TextAreaField'

const meta: Meta<typeof TextAreaField> = {
  component: TextAreaField,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/TextAreaField',
}
export default meta

type Story = StoryObj<typeof TextAreaField>

const Interactive = () => {
  const [value, setValue] = useState('')
  return (
    <TextAreaField
      label='Description'
      rows={3}
      placeholder='Describe…'
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
    <TextAreaField
      label='Description'
      required
      rows={3}
      placeholder='Describe…'
    />
  ),
}

export const WithError: Story = {
  render: () => (
    <TextAreaField
      label='Description'
      rows={3}
      value='Too short'
      error='Please add more detail.'
    />
  ),
}

export const Disabled: Story = {
  render: () => (
    <TextAreaField label='Description' rows={3} disabled value='Read only' />
  ),
}
