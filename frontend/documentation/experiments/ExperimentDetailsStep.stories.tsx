import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import ExperimentDetailsStep from 'components/experiments-v2/steps/ExperimentDetailsStep'
import { ExperimentDetails } from 'components/experiments-v2/types'

const meta: Meta<typeof ExperimentDetailsStep> = {
  component: ExperimentDetailsStep,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 600 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Steps/ExperimentDetailsStep',
}
export default meta

type Story = StoryObj<typeof ExperimentDetailsStep>

export const Empty: Story = {
  args: {
    details: { hypothesis: '', name: '', type: null },
    onChange: () => {},
  },
}

export const Filled: Story = {
  args: {
    details: {
      hypothesis:
        'Redesigning the checkout button with a clearer CTA will increase conversion rates by 15%',
      name: 'Checkout Flow Redesign',
      type: 'ab_test',
    },
    onChange: () => {},
  },
}

export const Interactive: Story = {
  decorators: [
    () => {
      const [details, setDetails] = useState<ExperimentDetails>({
        hypothesis: '',
        name: '',
        type: null,
      })
      return <ExperimentDetailsStep details={details} onChange={setDetails} />
    },
  ],
}
