import type { Meta, StoryObj } from 'storybook'
import { fireEvent } from 'storybook/test'

import LabelWithTooltip from 'components/base/LabelWithTooltip'

const meta: Meta<typeof LabelWithTooltip> = {
  args: {
    label: 'Server-side only',
    tooltip: 'Prevent this feature from being accessed with client-side SDKs.',
  },
  component: LabelWithTooltip,
  parameters: { layout: 'centered' },
  title: 'Components/Data Display/LabelWithTooltip',
}
export default meta

type Story = StoryObj<typeof LabelWithTooltip>

export const Default: Story = {}

export const WithoutTooltip: Story = {
  args: { label: 'Feature name', tooltip: undefined },
}

export const Hovered: Story = {
  parameters: {
    chromatic: { delay: 800 },
    docs: {
      description: { story: 'Tooltip in its visible state.' },
      story: { height: '160px' },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const trigger =
      canvasElement.querySelector<HTMLElement>('[data-tooltip-id]')
    if (!trigger) return
    // react-tooltip's pointer detection in Chromatic's headless Chrome
    // doesn't always pick up userEvent.hover; fire all four event
    // variants so whichever the library is listening for triggers.
    fireEvent.pointerEnter(trigger)
    fireEvent.pointerOver(trigger)
    fireEvent.mouseEnter(trigger)
    fireEvent.mouseOver(trigger)
  },
}
