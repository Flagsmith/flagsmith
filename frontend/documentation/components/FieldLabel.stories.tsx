import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import FieldLabel from 'components/base/forms/FieldLabel'

const meta: Meta<typeof FieldLabel> = {
  component: FieldLabel,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/FieldLabel',
}
export default meta

type Story = StoryObj<typeof FieldLabel>

export const Default: Story = {
  render: () => <FieldLabel htmlFor='email'>Email</FieldLabel>,
}

export const Required: Story = {
  render: () => (
    <FieldLabel htmlFor='email' required>
      Email
    </FieldLabel>
  ),
}

export const WithTooltip: Story = {
  render: () => (
    <FieldLabel htmlFor='email' tooltip='We never share your email.'>
      Email
    </FieldLabel>
  ),
}
