import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import ErrorState from 'components/warehouse/components/ErrorState'
import { MOCK_CONNECTION_DETAILS, MOCK_ERROR } from 'components/warehouse/types'

const meta: Meta<typeof ErrorState> = {
  component: ErrorState,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 800 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Warehouse/ErrorState',
}
export default meta

type Story = StoryObj<typeof ErrorState>

export const Default: Story = {
  args: {
    details: MOCK_CONNECTION_DETAILS,
    error: MOCK_ERROR,
    onEdit: () => alert('Edit'),
    onRetry: () => alert('Retry'),
  },
}
