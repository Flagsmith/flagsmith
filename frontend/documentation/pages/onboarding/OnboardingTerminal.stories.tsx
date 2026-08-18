import type { Meta, StoryObj } from 'storybook'

import OnboardingTerminal from 'components/pages/onboarding/OnboardingTerminal'

const meta: Meta<typeof OnboardingTerminal> = {
  args: {
    connected: false,
    featureName: 'show_demo_button',
    installCopied: false,
    snippetCopied: false,
  },
  component: OnboardingTerminal,
  parameters: {
    docs: {
      description: {
        component:
          'The onboarding verify console. The checklist ticks as the user acts (copy install, copy snippet), and the first evaluation flips the badge to LIVE and prints the connection receipt, naming the SDK that reported it when Core could identify it. Always dark, since a terminal reads the same in light and dark mode.',
      },
    },
    layout: 'padded',
  },
  title: 'Pages/Onboarding/OnboardingTerminal',
}
export default meta

type Story = StoryObj<typeof OnboardingTerminal>

export const Listening: Story = {}

export const InstallCopied: Story = {
  args: { installCopied: true },
}

export const SnippetsCopied: Story = {
  args: { installCopied: true, snippetCopied: true },
}

export const Connected: Story = {
  args: { connected: true, installCopied: true, snippetCopied: true },
}

// Core identifies the SDK from the user agent, so the receipt can name it.
export const ConnectedWithSdkLabel: Story = {
  args: {
    connected: true,
    installCopied: true,
    sdkLabel: 'flagsmith-python-sdk',
    snippetCopied: true,
  },
}
