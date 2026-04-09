import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import FlagVariationsStep from 'components/experiments-v2/steps/FlagVariationsStep'
import { MOCK_VARIATIONS, Variation } from 'components/experiments-v2/types'

const meta: Meta<typeof FlagVariationsStep> = {
  component: FlagVariationsStep,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 700 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Steps/FlagVariationsStep',
}
export default meta

type Story = StoryObj<typeof FlagVariationsStep>

export const Default: Story = {
  args: {
    featureFlagId: 'flag-1',
    onFlagChange: () => {},
    onVariationsChange: () => {},
    variations: MOCK_VARIATIONS,
  },
}

export const Interactive: Story = {
  decorators: [
    () => {
      const [flagId, setFlagId] = useState<string | null>('flag-1')
      const [variations, setVariations] = useState<Variation[]>(MOCK_VARIATIONS)
      return (
        <FlagVariationsStep
          featureFlagId={flagId}
          variations={variations}
          onFlagChange={setFlagId}
          onVariationsChange={setVariations}
        />
      )
    },
  ],
}
