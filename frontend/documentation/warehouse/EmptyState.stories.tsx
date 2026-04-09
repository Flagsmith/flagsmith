import type { Meta, StoryObj } from 'storybook'
import EmptyState from 'components/warehouse/components/EmptyState'

const meta: Meta<typeof EmptyState> = {
  component: EmptyState,
  tags: ['autodocs'],
  title: 'Warehouse/EmptyState',
}
export default meta

type Story = StoryObj<typeof EmptyState>

export const Default: Story = {
  args: { onConnect: () => alert('Connect') },
}
