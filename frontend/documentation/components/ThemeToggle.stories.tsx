import type { Meta, StoryObj } from 'storybook'

import ThemeToggle from 'components/ThemeToggle'

const meta: Meta<typeof ThemeToggle> = {
  component: ThemeToggle,
  parameters: {
    docs: {
      description: {
        component:
          'Always-visible theme control: an icon button showing the resolved theme, opening a Light / Dark / System menu. Selecting an option flips the theme live (including this Storybook canvas) and persists it.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/ThemeToggle',
}
export default meta

type Story = StoryObj<typeof ThemeToggle>

export const Default: Story = {}
