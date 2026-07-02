import type { Meta, StoryObj } from 'storybook'

import OnboardingNextSteps from 'components/pages/onboarding/OnboardingNextSteps'

const meta: Meta<typeof OnboardingNextSteps> = {
  args: {
    locked: false,
    onSelect: () => {},
  },
  component: OnboardingNextSteps,
  parameters: {
    docs: {
      description: {
        component:
          'The "Choose your next quest" section at the bottom of the onboarding flow: the three ways the demo flag can level up (gradual rollout, experiment, remote config), each linking to its real config. Locked and dimmed until the app connects.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingNextSteps',
}
export default meta

type Story = StoryObj<typeof OnboardingNextSteps>

export const Connected: Story = {}

export const Locked: Story = {
  args: { locked: true },
}
