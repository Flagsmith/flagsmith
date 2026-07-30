import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Field from 'components/base/forms/Field'
import Input from 'components/base/forms/Input'

const meta: Meta<typeof Field> = {
  component: Field,
  decorators: [
    (Story: React.FC) => (
      <div style={{ width: 320 }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        component:
          'The field skeleton: wrapper, label, control, error. Layout only; pass `htmlFor` (and put the matching `id` on the control) to wire the label, or omit it as a visible statement that the label is decorative.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Forms/Field',
}
export default meta

type Story = StoryObj<typeof Field>

// Declaring htmlFor once wires everything: Input adopts it as its id via
// FieldContext, and picks up aria-invalid/aria-describedby when there is
// an error.
export const Default: Story = {
  render: () => (
    <Field title='Email' htmlFor='field-email'>
      <Input placeholder='you@example.com' />
    </Field>
  ),
}

export const WithTooltip: Story = {
  render: () => (
    <Field
      title='Email'
      tooltip='We never share your email.'
      htmlFor='field-email-tooltip'
    >
      <Input placeholder='you@example.com' />
    </Field>
  ),
}

export const WithError: Story = {
  render: () => (
    <Field
      title='Email'
      htmlFor='field-email-error'
      error='Enter a valid email address.'
    >
      <Input isValid={false} autoValidate value='not-an-email' />
    </Field>
  ),
}

export const CustomControl: Story = {
  render: () => (
    <Field title='Colour' tooltip='No htmlFor: the swatches take no id.'>
      <div className='d-flex gap-2'>
        {['#5D6D7E', '#27AB95', '#F7D354'].map((c) => (
          <div
            key={c}
            style={{ background: c, borderRadius: 4, height: 24, width: 24 }}
          />
        ))}
      </div>
    </Field>
  ),
}
