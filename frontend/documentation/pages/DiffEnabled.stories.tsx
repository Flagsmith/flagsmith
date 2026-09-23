import type { Meta, StoryObj } from 'storybook'

import DiffEnabled from 'components/diff/DiffEnabled'

const meta: Meta<typeof DiffEnabled> = {
  component: DiffEnabled,
  parameters: {
    docs: {
      description: {
        component:
          'The diff view for a flag or segment override being turned on or off.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Diff/DiffEnabled',
}

export default meta

type Story = StoryObj<typeof DiffEnabled>

export const OffToOn: Story = {
  args: { newValue: true, oldValue: false },
}

export const OnToOff: Story = {
  args: { newValue: false, oldValue: true },
}

export const Unchanged: Story = {
  args: { newValue: true, oldValue: true },
}
