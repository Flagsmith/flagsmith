import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import OnboardingTabs, {
  OnboardingTab,
} from 'components/pages/onboarding/OnboardingTabs'

const meta: Meta<typeof OnboardingTabs> = {
  component: OnboardingTabs,
  parameters: {
    docs: {
      description: {
        component:
          "One-off onboarding tablist following the WAI-ARIA tabs pattern: roving tabindex, Arrow/Home/End keys, aria-selected. A tab can be pushed to the trailing edge with `alignEnd` - the reason this isn't the shared navigation Tabs. Local to onboarding; pair with OnboardingTabPanel for the content side.",
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingTabs',
}
export default meta

type Story = StoryObj<typeof OnboardingTabs>

const Controlled = ({ tabs }: { tabs: OnboardingTab[] }) => {
  const [active, setActive] = useState(tabs[0].id)
  return (
    <OnboardingTabs
      aria-label='Connect your app'
      tabs={tabs}
      activeId={active}
      onChange={setActive}
    />
  )
}

export const Default: Story = {
  render: () => (
    <Controlled
      tabs={[
        { id: 'manual', label: 'Connect your code' },
        { alignEnd: true, id: 'ai', label: 'Connect with AI' },
      ]}
    />
  ),
}

export const ThreeTabs: Story = {
  render: () => (
    <Controlled
      tabs={[
        { id: 'one', label: 'First' },
        { id: 'two', label: 'Second' },
        { alignEnd: true, id: 'three', label: 'Third' },
      ]}
    />
  ),
}
