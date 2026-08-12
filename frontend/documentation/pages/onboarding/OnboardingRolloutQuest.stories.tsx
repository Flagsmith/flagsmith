import type { Meta, StoryObj } from 'storybook'

import OnboardingRolloutQuest from 'components/pages/onboarding/OnboardingRolloutQuest'

const meta: Meta<typeof OnboardingRolloutQuest> = {
  args: {
    featureName: 'checkout_v2',
    onContinue: () => {},
    onDismiss: () => {},
    onFeedback: () => {},
    onNotifyMe: () => {},
  },
  component: OnboardingRolloutQuest,
  parameters: {
    docs: {
      description: {
        component:
          'The "Gradual rollout" quest, shown between the next-step card and the flag\'s segment overrides tab. Explains the three manual steps a rollout takes today, flags the identify prerequisite, and gauges demand for doing it in one action.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingRolloutQuest',
}
export default meta

type Story = StoryObj<typeof OnboardingRolloutQuest>

export const Default: Story = {}

// The flag name threads through the subtitle and step 2.
export const LongFeatureName: Story = {
  args: { featureName: 'enable_new_checkout_experience_for_mobile' },
}
