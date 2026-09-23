import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import FieldError from 'components/base/forms/FieldError'

const meta: Meta<typeof FieldError> = {
  component: FieldError,
  parameters: { layout: 'padded' },
  title: 'Components/Forms/FieldError',
}
export default meta

type Story = StoryObj<typeof FieldError>

export const Default: Story = {
  render: () => <FieldError error='This field is required.' />,
}

export const RichMessage: Story = {
  render: () => (
    <FieldError
      error={
        <>
          Must be a valid <strong>email address</strong>.
        </>
      }
    />
  ),
}
