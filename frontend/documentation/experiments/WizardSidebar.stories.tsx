import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import WizardSidebar from 'components/experiments-v2/wizard/WizardSidebar'
import { EXPERIMENT_WIZARD_STEPS } from 'components/experiments-v2/types'

const meta: Meta<typeof WizardSidebar> = {
  args: {
    steps: EXPERIMENT_WIZARD_STEPS,
  },
  component: WizardSidebar,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 280 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Wizard/WizardSidebar',
}
export default meta

type Story = StoryObj<typeof WizardSidebar>

export const Step1Active: Story = {
  args: { currentStep: 0 },
}

export const Step3Active: Story = {
  args: {
    currentStep: 2,
    steps: EXPERIMENT_WIZARD_STEPS.map((s, i) => {
      let completeSummary: string | undefined
      if (i === 0) completeSummary = 'Checkout Flow Redesign · A/B Test'
      else if (i === 1) completeSummary = '1 primary · 2 secondary'
      return { ...s, completeSummary }
    }),
  },
}

export const AllDone: Story = {
  args: {
    currentStep: 5,
    steps: EXPERIMENT_WIZARD_STEPS.map((s, i) => ({
      ...s,
      completeSummary: `Step ${i + 1} complete`,
    })),
  },
}
