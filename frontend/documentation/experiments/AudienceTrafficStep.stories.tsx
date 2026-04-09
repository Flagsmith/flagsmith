import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import AudienceTrafficStep from 'components/experiments-v2/steps/AudienceTrafficStep'
import {
  AudienceConfig,
  MOCK_VARIATIONS,
} from 'components/experiments-v2/types'

const meta: Meta<typeof AudienceTrafficStep> = {
  component: AudienceTrafficStep,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 600 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Steps/AudienceTrafficStep',
}
export default meta

type Story = StoryObj<typeof AudienceTrafficStep>

export const Default: Story = {
  args: {
    audience: { segmentId: null, splits: [], trafficPercentage: 50 },
    onChange: () => {},
    variations: MOCK_VARIATIONS,
  },
}

export const Interactive: Story = {
  decorators: [
    () => {
      const [audience, setAudience] = useState<AudienceConfig>({
        segmentId: 'seg-1',
        splits: [],
        trafficPercentage: 50,
      })
      return (
        <AudienceTrafficStep
          audience={audience}
          variations={MOCK_VARIATIONS}
          onChange={setAudience}
        />
      )
    },
  ],
}
