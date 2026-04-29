import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { userEvent, within } from 'storybook/test'

import Tooltip from 'components/Tooltip'

const meta: Meta = {
  parameters: {
    chromatic: { delay: 300 },
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

export const Default: Story = {
  parameters: {
    docs: { story: { height: '160px' } },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    await userEvent.hover(within(canvasElement).getByText('Hover me'))
  },
  render: () => (
    <Tooltip title={<span>Hover me</span>}>
      This is the tooltip content.
    </Tooltip>
  ),
}

export const PlainText: Story = {
  parameters: {
    docs: { story: { height: '160px' } },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    await userEvent.hover(within(canvasElement).getByText('Plain text tooltip'))
  },
  render: () => (
    <Tooltip title={<span>Plain text tooltip</span>} plainText>
      Simple text without HTML rendering.
    </Tooltip>
  ),
}
