import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import InfoMessage from 'components/InfoMessage'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Inline alert for informational messages. Supports an optional title, an action button, a manual close button, and a chevron that lets the user collapse the message — useful for inline help or announcement banners.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Feedback/InfoMessage',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <InfoMessage>
      This will create the feature for <strong>all environments</strong>.
    </InfoMessage>
  ),
}

export const WithTitle: Story = {
  render: () => (
    <InfoMessage title='Heads up'>
      Changing this setting affects all environments in the project.
    </InfoMessage>
  ),
}

export const Closable: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Caller-managed dismissal. Pass `isClosable` to render the close button and `close` to handle the dismissal — typical for one-off announcement banners.',
      },
    },
  },
  render: () => (
    <InfoMessage isClosable close={() => {}}>
      You can dismiss this message.
    </InfoMessage>
  ),
}

export const Collapsible: Story = {
  parameters: {
    docs: {
      description: {
        story:
          "Pass `collapseId` to make the message collapsible via a chevron toggle in the header. The open/closed state is persisted in `localStorage` keyed by the id, so the user's choice sticks across sessions. This is the most common dismissal pattern in the app — used for inline help blocks that experienced users want to roll up.",
      },
    },
  },
  render: () => (
    <InfoMessage
      collapseId='storybook-info-message-demo'
      title='Local evaluation mode'
    >
      In local evaluation mode the SDK fetches the entire environment document
      and evaluates flags client-side, reducing latency and removing per-flag
      network round-trips.
    </InfoMessage>
  ),
}

export const WithAction: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Pass `buttonText` + `url` to embed an action button that opens the URL in a new tab — used by announcement banners.',
      },
    },
  },
  render: () => (
    <InfoMessage
      title="What's new"
      buttonText='Read more'
      url='https://flagsmith.com/blog'
    >
      Flagsmith now supports SAML SSO for all enterprise plans.
    </InfoMessage>
  ),
}
