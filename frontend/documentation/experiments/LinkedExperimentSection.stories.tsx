import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import LinkedExperimentSection from 'components/experiments-v2/flag-detail/LinkedExperimentSection'
import { MOCK_LINKED_EXPERIMENT } from 'components/experiments-v2/types'

const meta: Meta<typeof LinkedExperimentSection> = {
  component: LinkedExperimentSection,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 600 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/LinkedExperimentSection',
}
export default meta

type Story = StoryObj<typeof LinkedExperimentSection>

export const WithExperiment: Story = {
  args: {
    experiment: MOCK_LINKED_EXPERIMENT,
    onViewResults: () => alert('View results'),
  },
}

export const Empty: Story = {
  args: {
    experiment: null,
    onCreateExperiment: () => alert('Create experiment'),
  },
}
