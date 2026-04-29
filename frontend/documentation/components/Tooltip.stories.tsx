import React from 'react'
import type { Meta, StoryObj } from 'storybook'
import { fireEvent } from 'storybook/test'

import Tooltip from 'components/Tooltip'

const meta: Meta = {
  parameters: {
    chromatic: { delay: 800 },
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

const hoverFirstTooltip = ({
  canvasElement,
}: {
  canvasElement: HTMLElement
}) => {
  const trigger = canvasElement.querySelector<HTMLElement>('[data-tooltip-id]')
  if (!trigger) return
  // react-tooltip's pointer detection in Chromatic's headless Chrome
  // doesn't always fire from userEvent.hover; dispatch all four event
  // variants so whichever the library is listening for triggers.
  fireEvent.pointerEnter(trigger)
  fireEvent.pointerOver(trigger)
  fireEvent.mouseEnter(trigger)
  fireEvent.mouseOver(trigger)
}

export const Default: Story = {
  parameters: {
    docs: { story: { height: '160px' } },
  },
  play: hoverFirstTooltip,
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
  play: hoverFirstTooltip,
  render: () => (
    <Tooltip title={<span>Plain text tooltip</span>} plainText>
      Simple text without HTML rendering.
    </Tooltip>
  ),
}
