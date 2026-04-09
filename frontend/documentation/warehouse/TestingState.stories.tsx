import type { Meta, StoryObj } from 'storybook'
import TestingState from 'components/warehouse/components/TestingState'

const meta: Meta<typeof TestingState> = {
  component: TestingState,
  tags: ['autodocs'],
  title: 'Warehouse/TestingState',
}
export default meta

type Story = StoryObj<typeof TestingState>

export const AllStepsComplete: Story = {
  args: { currentStep: 4 },
}

export const MidProgress: Story = {
  args: { currentStep: 2 },
}
