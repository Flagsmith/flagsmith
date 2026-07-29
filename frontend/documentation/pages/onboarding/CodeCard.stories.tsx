import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import CodeCard from 'components/pages/onboarding/OnboardingConnectPanel/CodeCard'
// CodeCard's structural styles (radius, header, lang label) live in the connect
// panel's stylesheet; import it so the card renders fully styled in isolation.
import 'components/pages/onboarding/OnboardingConnectPanel/OnboardingConnectPanel.scss'

const meta: Meta<typeof CodeCard> = {
  args: {
    code: 'npm install flagsmith',
    headerLeft: (
      <span className='onboarding-connect__codecard-lang'>Shell</span>
    ),
    language: 'bash',
  },
  component: CodeCard,
  parameters: {
    docs: {
      description: {
        component:
          'A copyable, syntax-highlighted code block with a header strip. Owns its own "Copied" feedback (announced via aria-live) and is theme-adaptive via semantic tokens - a light editor in light mode, dark in dark mode.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/CodeCard',
}
export default meta

type Story = StoryObj<typeof CodeCard>

export const Install: Story = {}

export const Wire: Story = {
  args: {
    code: "import flagsmith from 'flagsmith'\nflagsmith.init({ environmentID: 'ser.abc123EXAMPLEkey' })\nconst showDemo = flagsmith.hasFeature('show_demo_button')",
    headerLeft: (
      <span className='onboarding-connect__codecard-lang'>JavaScript</span>
    ),
    language: 'javascript',
  },
}
