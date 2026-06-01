import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import ErrorMessage from 'components/ErrorMessage'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Inline alert for API errors. Pass the raw error response and the component will surface a readable message; renders nothing when the error is falsy.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Feedback/ErrorMessage',
}
export default meta

type Story = StoryObj

export const StringError: Story = {
  render: () => <ErrorMessage error='Something went wrong.' />,
}

export const ApiErrorWithData: Story = {
  render: () => (
    <ErrorMessage error={{ data: 'Feature with this name already exists.' }} />
  ),
}

export const ApiErrorWithMessage: Story = {
  render: () => (
    <ErrorMessage
      error={{ message: 'Network request failed. Please try again.' }}
    />
  ),
}

export const NonFieldErrors: Story = {
  render: () => (
    <ErrorMessage
      error={{
        data: {
          metadata: [
            { non_field_errors: ['You do not have permission to do this.'] },
          ],
        },
      }}
    />
  ),
}
