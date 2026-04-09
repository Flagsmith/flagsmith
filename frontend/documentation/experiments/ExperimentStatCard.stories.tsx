import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import ExperimentStatCard from 'components/experiments-v2/shared/ExperimentStatCard'

const meta: Meta<typeof ExperimentStatCard> = {
  component: ExperimentStatCard,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 250 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/ExperimentStatCard',
}
export default meta

type Story = StoryObj<typeof ExperimentStatCard>

export const Default: Story = {
  args: { label: 'Users Enrolled', value: 12847 },
}

export const Positive: Story = {
  args: {
    label: 'Winning Variation',
    trend: 'positive',
    value: 'Treatment B',
  },
}

export const WithSubtitle: Story = {
  args: {
    label: 'Lift vs Control',
    subtitle: 'vs control group',
    trend: 'positive',
    value: '+18.3%',
  },
}
