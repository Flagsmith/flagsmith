import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import ReviewLaunchStep from 'components/experiments-v2/steps/ReviewLaunchStep'
import {
  ExperimentWizardState,
  MOCK_METRICS,
  MOCK_VARIATIONS,
} from 'components/experiments-v2/types'

const MOCK_WIZARD_STATE: ExperimentWizardState = {
  audience: {
    segmentId: 'seg-1',
    splits: [],
    trafficPercentage: 50,
  },
  currentStep: 4,
  details: {
    hypothesis:
      'Redesigning the checkout button will increase conversions by 15%',
    name: 'Checkout Flow Redesign',
    type: 'ab_test',
  },
  featureFlagId: 'flag-1',
  metrics: [MOCK_METRICS[0], { ...MOCK_METRICS[1], role: 'secondary' }],
  variations: MOCK_VARIATIONS,
}

const meta: Meta<typeof ReviewLaunchStep> = {
  component: ReviewLaunchStep,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 600 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Steps/ReviewLaunchStep',
}
export default meta

type Story = StoryObj<typeof ReviewLaunchStep>

export const FullReview: Story = {
  args: {
    onEditStep: (step: number) => alert(`Edit step ${step}`),
    wizardState: MOCK_WIZARD_STATE,
  },
}
