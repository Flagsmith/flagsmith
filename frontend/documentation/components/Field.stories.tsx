import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Field from 'components/base/forms/Field'
import Input from 'components/base/forms/Input'

const meta: Meta<typeof Field> = {
  component: Field,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/Field',
}
export default meta

type Story = StoryObj<typeof Field>

export const Default: Story = {
  render: () => (
    <Field label='Email' htmlFor='field-default'>
      <Input id='field-default' placeholder='you@example.com' />
    </Field>
  ),
}

export const WithError: Story = {
  render: () => (
    <Field label='Email' htmlFor='field-error' error='Enter a valid email.'>
      <Input id='field-error' value='nope' isValid={false} autoValidate />
    </Field>
  ),
}

export const RequiredWithTooltip: Story = {
  render: () => (
    <Field
      label='Email'
      htmlFor='field-required'
      required
      tooltip='We never share your email.'
    >
      <Input id='field-required' placeholder='you@example.com' />
    </Field>
  ),
}

// Field wraps any control, not just Input (this replaces InputGroup's
// `component=`).
export const CustomControl: Story = {
  render: () => (
    <Field label='Notes' htmlFor='field-custom'>
      <textarea
        id='field-custom'
        className='input full-width'
        rows={3}
        placeholder='Any control goes here'
      />
    </Field>
  ),
}
