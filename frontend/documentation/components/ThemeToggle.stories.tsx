import type { Meta, StoryObj } from 'storybook'

import ThemeToggle from 'components/ThemeToggle'

const meta: Meta<typeof ThemeToggle> = {
  component: ThemeToggle,
  parameters: {
    docs: {
      description: {
        component:
          'One-click light/dark toggle (the icon shows what you switch to). With no stored choice the theme follows the OS; the first click pins an explicit preference. Clicking flips this Storybook canvas live.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/ThemeToggle',
}
export default meta

type Story = StoryObj<typeof ThemeToggle>

export const Default: Story = {}
