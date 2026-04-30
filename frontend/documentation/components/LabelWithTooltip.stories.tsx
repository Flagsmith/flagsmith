import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, waitFor } from 'storybook/test'

import LabelWithTooltip from 'components/base/LabelWithTooltip'

const meta: Meta<typeof LabelWithTooltip> = {
  args: {
    label: 'Server-side only',
    tooltip: 'Prevent this feature from being accessed with client-side SDKs.',
  },
  component: LabelWithTooltip,
  parameters: { layout: 'centered' },
  title: 'Components/Forms/LabelWithTooltip',
}
export default meta

type Story = StoryObj<typeof LabelWithTooltip>

export const Default: Story = {}

export const WithoutTooltip: Story = {
  args: { label: 'Feature name', tooltip: undefined },
}

export const Hovered: Story = {
  decorators: [
    (StoryFn: React.ComponentType) => (
      <div className='pt-5 pl-5 pr-5'>
        <StoryFn />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: { story: 'Tooltip in its visible state.' },
      story: { height: '200px' },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    // Wait for the nested Tooltip's useEffect to register the
    // react-tooltip anchor before hovering.
    await new Promise((resolve) => setTimeout(resolve, 100))
    const trigger =
      canvasElement.querySelector<HTMLElement>('[data-tooltip-id]')
    if (!trigger) return
    await userEvent.hover(trigger)
    await waitFor(
      () => {
        if (!document.body.querySelector('[role="tooltip"]')) {
          throw new Error('tooltip popover not yet visible')
        }
      },
      { timeout: 2000 },
    )
  },
}
