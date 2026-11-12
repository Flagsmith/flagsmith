import type { Meta, StoryObj } from 'storybook'

import { Tag } from 'common/types/responses'
import OnboardingFlagsTable, {
  OnboardingFlagRow,
} from 'components/pages/onboarding/OnboardingFlagsTable'

const demoFlag: OnboardingFlagRow = {
  description: 'Controls the demo button shown to your users',
  enabled: true,
  name: 'show_demo_button',
}

const meta: Meta<typeof OnboardingFlagsTable> = {
  args: {
    flags: [demoFlag],
    onToggle: () => {},
    status: 'connected',
  },
  component: OnboardingFlagsTable,
  parameters: {
    docs: {
      description: {
        component:
          'The "Your flags" card from the onboarding flow, reusing the product FeatureName / Tag / Switch. Prop-driven: the page owns the flag data and the persisted Dev toggle. `connected` lifts the card with the accent border and glow; `waiting` dims it until the first evaluation arrives.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingFlagsTable',
}
export default meta

type Story = StoryObj<typeof OnboardingFlagsTable>

export const Connected: Story = {}

export const Waiting: Story = {
  args: { status: 'waiting' },
}

export const Off: Story = {
  args: { flags: [{ ...demoFlag, enabled: false }] },
}

export const WithTag: Story = {
  args: {
    flags: [
      { ...demoFlag, tags: [{ color: '#6837FC', label: 'demo' } as Tag] },
    ],
  },
}
