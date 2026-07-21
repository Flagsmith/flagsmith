import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import WarningMessage from 'components/WarningMessage'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Inline alert for warnings — softer than `ErrorMessage`, used to flag deprecations, approaching limits, or actions that need attention. Renders nothing when `warningMessage` is empty.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Feedback/WarningMessage',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <WarningMessage warningMessage='This feature is deprecated and will be removed.' />
  ),
}

export const WithCustomClass: Story = {
  render: () => (
    <WarningMessage
      warningMessage='You have reached 80% of your identity limit.'
      warningMessageClass='text-center'
    />
  ),
}
