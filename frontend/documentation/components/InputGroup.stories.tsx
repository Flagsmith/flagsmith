import React, { ComponentProps, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import InputGroup from 'components/base/forms/InputGroup'

// Stateful wrapper so the field is controlled in the story (InputGroup forwards
// value/onChange to the underlying control).
type FieldProps = ComponentProps<typeof InputGroup> & { initialValue?: string }

const Field = ({ initialValue, ...props }: FieldProps) => {
  const [value, setValue] = useState(initialValue ?? '')
  return (
    <InputGroup
      {...props}
      value={value}
      onChange={(
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
      ) => setValue(e.target.value)}
    />
  )
}

const meta: Meta<typeof InputGroup> = {
  component: InputGroup,
  decorators: [
    (Story: React.FC) => (
      <div style={{ width: 320 }}>
        <Story />
      </div>
    ),
  ],
  parameters: { layout: 'centered' },
  title: 'Components/Forms/InputGroup',
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => <Field title='Email' placeholder='you@example.com' />,
}

// Info-icon tooltip after the label — the icon sits centred against the text.
export const WithTooltip: Story = {
  render: () => (
    <Field
      title='Email'
      tooltip='We never share your email.'
      placeholder='you@example.com'
    />
  ),
}

export const WithError: Story = {
  render: () => (
    <Field
      title='Email'
      initialValue='not-an-email'
      isValid={false}
      inputProps={{ error: 'Enter a valid email address.', name: 'email' }}
    />
  ),
}

export const MultipleErrors: Story = {
  render: () => (
    <Field
      title='Password'
      type='password'
      initialValue='abc'
      isValid={false}
      inputProps={{
        error: ['At least 8 characters', 'Must include a number'],
        name: 'password',
      }}
    />
  ),
}

export const Disabled: Story = {
  render: () => <Field title='Email' initialValue='you@example.com' disabled />,
}

export const Textarea: Story = {
  render: () => (
    <Field textarea title='Description' initialValue='A short description…' />
  ),
}

// "Unsaved" badge beside the label, used when a field has pending changes.
export const Unsaved: Story = {
  render: () => <Field title='Display name' unsaved initialValue='Jane' />,
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <Field size='large' title='Large' placeholder='Large' />
      <Field title='Default' placeholder='Default' />
      <Field size='small' title='Small' placeholder='Small' />
      <Field size='xSmall' title='xSmall' placeholder='xSmall' />
    </div>
  ),
}
