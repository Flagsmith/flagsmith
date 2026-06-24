import type { Meta, StoryObj } from 'storybook'

import OnboardingHeader from 'components/pages/onboarding/OnboardingHeader'

const meta: Meta<typeof OnboardingHeader> = {
  args: {
    caseSensitive: true,
    featureName: 'show_demo_button',
    organisationName: 'Acme Inc',
    projectName: 'Web App',
  },
  component: OnboardingHeader,
  parameters: {
    docs: {
      description: {
        component:
          'The top of the single-page onboarding flow: a welcome title and a sentence naming the resources we pre-created, with organisation / project / flag inline-editable in place via the shared GhostInput. Presentational - the rename handlers are owned by the page that assembles the flow.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingHeader',
}
export default meta

type Story = StoryObj<typeof OnboardingHeader>

export const Default: Story = {}

export const LongNames: Story = {
  args: {
    featureName: 'enable_the_brand_new_checkout_experience_v2',
    organisationName: 'A Very Long Organisation Name That Wraps',
    projectName: 'Customer-Facing Marketing Website Project',
  },
}

export const ShortNames: Story = {
  args: {
    featureName: 'beta',
    organisationName: 'Co',
    projectName: 'App',
  },
}
