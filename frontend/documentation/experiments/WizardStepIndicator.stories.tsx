import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import WizardStepIndicator from 'components/experiments-v2/wizard/WizardStepIndicator'

const meta: Meta<typeof WizardStepIndicator> = {
  args: {
    showConnector: true,
    stepNumber: 1,
    subtitle: 'Define the basics of your experiment',
    title: 'Experiment Details',
  },
  component: WizardStepIndicator,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 400 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Wizard/WizardStepIndicator',
}
export default meta

type Story = StoryObj<typeof WizardStepIndicator>

export const Done: Story = {
  args: {
    completeSummary: 'Checkout Flow Redesign · A/B Test',
    onClick: () => alert('Step clicked'),
    status: 'done',
  },
}

export const Active: Story = {
  args: {
    status: 'active',
    stepNumber: 2,
    subtitle: 'Choose primary and secondary metrics to measure',
    title: 'Select Metrics',
  },
}

export const Upcoming: Story = {
  args: {
    showConnector: false,
    status: 'upcoming',
    stepNumber: 5,
    subtitle: 'Review your configuration and launch',
    title: 'Review & Launch',
  },
}
