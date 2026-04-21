import type { Meta, StoryObj } from 'storybook'
import StatItem from 'components/StatItem'

const meta: Meta<typeof StatItem> = {
  component: StatItem,
  tags: ['autodocs'],
  title: 'Components/StatItem',
}
export default meta

type Story = StoryObj<typeof StatItem>

export const Default: Story = {
  args: {
    icon: 'features',
    label: 'Flags',
    value: 437008,
  },
}

export const WithLimit: Story = {
  args: {
    icon: 'bar-chart',
    label: 'Total API Calls',
    limit: 50000000,
    value: 4569636,
  },
}

export const WithTooltip: Story = {
  args: {
    icon: 'bar-chart',
    label: 'Total API Calls',
    tooltip: 'Your plan limit is 50,000,000 / month',
    value: 4569636,
  },
}

export const WithVisibilityToggle: Story = {
  args: {
    icon: 'person',
    label: 'Identities',
    value: 2162461,
    visibilityToggle: {
      colour: '#27AB95',
      isVisible: true,
      onToggle: () => {},
    },
  },
}

export const StringValue: Story = {
  args: {
    icon: 'layers',
    label: 'Plan',
    value: 'Scale-Up',
  },
}
