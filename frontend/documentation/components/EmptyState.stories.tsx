import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import EmptyState from 'components/EmptyState'
import Button from 'components/base/forms/Button'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Components/Feedback/EmptyState',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <EmptyState
      title='No features yet'
      description='Create your first feature flag to get started.'
      icon='features'
    />
  ),
}

export const WithAction: Story = {
  render: () => (
    <EmptyState
      title='No segments found'
      description='Segments let you target specific users.'
      icon='people'
      action={<Button theme='primary'>Create segment</Button>}
    />
  ),
}
