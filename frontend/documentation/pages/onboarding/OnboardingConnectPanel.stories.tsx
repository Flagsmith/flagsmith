import type { Meta, StoryObj } from 'storybook'

import OnboardingConnectPanel from 'components/pages/onboarding/OnboardingConnectPanel'

const meta: Meta<typeof OnboardingConnectPanel> = {
  args: {
    environmentKey: 'ser.abc123EXAMPLEkey',
    featureName: 'show_demo_button',
  },
  component: OnboardingConnectPanel,
  parameters: {
    docs: {
      description: {
        component:
          'Two ways to connect an app to the pre-created flag: a "Connect with AI" tab (an agent-agnostic, zero-auth prompt carrying the real env key + flag) and a "Connect your code" tab (an SDK selector built on Chip, with install + wire snippets per language). Nothing is faked - the prompt and snippets carry the user\'s real env key + flag.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingConnectPanel',
}
export default meta

type Story = StoryObj<typeof OnboardingConnectPanel>

export const Default: Story = {}

export const CustomFlagName: Story = {
  args: { featureName: 'enable_new_checkout' },
}
