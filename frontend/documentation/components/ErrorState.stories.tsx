import { ComponentProps } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ErrorState from 'components/ErrorState'

type ErrorStateProps = ComponentProps<typeof ErrorState>

const meta: Meta<ErrorStateProps> = {
  args: {
    description:
      'Something went wrong fetching this list. Try again in a moment.',
    title: 'Features could not be loaded',
  },
  component: ErrorState,
  parameters: { layout: 'padded' },
  title: 'Components/Feedback/ErrorState',
}
export default meta

type Story = StoryObj<ErrorStateProps>

export const WithRetry: Story = {
  args: { onRetry: () => {} },
}

// Nothing to retry, such as a failure the user cannot fix from here.
export const WithoutRetry: Story = {}

export const WithIcon: Story = {
  args: {
    description:
      'Something went wrong fetching usage for this period. Try again in a moment.',
    icon: 'bar-chart',
    onRetry: () => {},
    title: 'Usage could not be loaded',
  },
}
