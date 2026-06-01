import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Top-of-page header with a title, optional description (`children`), and an optional `cta` slot for a primary action. Standard pattern at the top of every list/dashboard page.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Patterns/PageTitle',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => <PageTitle title='Features' />,
}

export const WithDescription: Story = {
  render: () => (
    <PageTitle title='Features'>
      Manage your feature flags across all environments.
    </PageTitle>
  ),
}

export const WithCTA: Story = {
  render: () => (
    <PageTitle
      title='Features'
      cta={<Button theme='primary'>Create Feature</Button>}
    >
      Manage your feature flags across all environments.
    </PageTitle>
  ),
}
