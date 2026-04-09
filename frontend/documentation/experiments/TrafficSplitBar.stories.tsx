import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import TrafficSplitBar from 'components/experiments-v2/shared/TrafficSplitBar'

const meta: Meta<typeof TrafficSplitBar> = {
  component: TrafficSplitBar,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 500 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/TrafficSplitBar',
}
export default meta

type Story = StoryObj<typeof TrafficSplitBar>

export const EvenSplit: Story = {
  args: {
    splits: [
      { colour: 'var(--green-500)', name: 'Control', percentage: 50 },
      { colour: 'var(--purple-500)', name: 'Treatment B', percentage: 50 },
    ],
  },
}

export const UnevenSplit: Story = {
  args: {
    splits: [
      { colour: 'var(--green-500)', name: 'Control', percentage: 30 },
      { colour: 'var(--purple-500)', name: 'Treatment B', percentage: 50 },
      { colour: 'var(--orange-500)', name: 'Treatment C', percentage: 20 },
    ],
  },
}
