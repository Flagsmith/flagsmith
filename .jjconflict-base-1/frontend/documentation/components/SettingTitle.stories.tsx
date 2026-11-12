import type { Meta, StoryObj } from 'storybook'

import SettingTitle from 'components/SettingTitle'

const meta: Meta<typeof SettingTitle> = {
  args: { children: 'General Settings', danger: false },
  component: SettingTitle,
  parameters: { layout: 'padded' },
  title: 'Components/Data Display/SettingTitle',
}
export default meta

type Story = StoryObj<typeof SettingTitle>

export const Default: Story = {}

export const Danger: Story = {
  args: { children: 'Danger Zone', danger: true },
}
