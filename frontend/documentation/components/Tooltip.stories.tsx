import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, waitFor } from 'storybook/test'

import Tooltip from 'components/Tooltip'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Floating popover with a hover/focus trigger. Wrap a trigger element in `title`; the children become the tooltip content. Defaults to rendering content as HTML — pass `plainText` to escape it instead.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/Tooltip',
}
export default meta

type Story = StoryObj

const hoverFirstTooltip = async ({
  canvasElement,
}: {
  canvasElement: HTMLElement
}) => {
  const trigger = canvasElement.querySelector<HTMLElement>('[data-tooltip-id]')
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
}

export const Default: Story = {
  parameters: {
    docs: { story: { height: '200px' } },
  },
  play: hoverFirstTooltip,
  render: () => (
    <div className='pt-5'>
      <Tooltip title={<span>Hover me</span>}>
        This is the tooltip content.
      </Tooltip>
    </div>
  ),
}

export const PlainText: Story = {
  parameters: {
    docs: { story: { height: '200px' } },
  },
  play: hoverFirstTooltip,
  render: () => (
    <div className='pt-5'>
      <Tooltip title={<span>Plain text tooltip</span>} plainText>
        Simple text without HTML rendering.
      </Tooltip>
    </div>
  ),
}
