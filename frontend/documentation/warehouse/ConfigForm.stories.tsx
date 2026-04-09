import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import ConfigForm from 'components/warehouse/components/ConfigForm'

const meta: Meta<typeof ConfigForm> = {
  component: ConfigForm,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 700 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Warehouse/ConfigForm',
}
export default meta

type Story = StoryObj<typeof ConfigForm>

export const Default: Story = {
  args: {
    onCancel: () => alert('Cancel'),
    onTestConnection: (config) => alert(`Test: ${config.accountUrl}`),
  },
}
