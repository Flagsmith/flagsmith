import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import ConnectedState from 'components/warehouse/components/ConnectedState'
import { MOCK_CONNECTION_DETAILS, MOCK_STATS } from 'components/warehouse/types'

const meta: Meta<typeof ConnectedState> = {
  component: ConnectedState,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 800 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Warehouse/ConnectedState',
}
export default meta

type Story = StoryObj<typeof ConnectedState>

export const Default: Story = {
  args: {
    details: MOCK_CONNECTION_DETAILS,
    onDisconnect: () => alert('Disconnect'),
    onEdit: () => alert('Edit'),
    stats: MOCK_STATS,
  },
}
