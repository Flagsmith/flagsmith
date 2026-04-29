import type { Meta, StoryObj } from 'storybook'
import { userEvent } from 'storybook/test'

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
    chromatic: { delay: 300 },
    docs: {
      description: { story: 'Tooltip in its visible state.' },
      story: { height: '160px' },
    },
  },
  play: async ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const trigger = canvasElement.querySelector('[data-tooltip-id]')
    if (trigger) await userEvent.hover(trigger as HTMLElement)
  },
}
