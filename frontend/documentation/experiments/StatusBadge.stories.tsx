import type { Meta, StoryObj } from 'storybook'
import StatusBadge from 'components/experiments-v2/shared/StatusBadge'

const meta: Meta<typeof StatusBadge> = {
  component: StatusBadge,
  tags: ['autodocs'],
  title: 'Experiments/StatusBadge',
}
export default meta

type Story = StoryObj<typeof StatusBadge>

export const Running: Story = { args: { status: 'running' } }
export const Paused: Story = { args: { status: 'paused' } }
export const Completed: Story = { args: { status: 'completed' } }
