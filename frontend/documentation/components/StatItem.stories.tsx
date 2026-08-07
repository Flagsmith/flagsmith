import type { Meta, StoryObj } from 'storybook'
import StatItem from 'components/StatItem'
import StatusBadge from 'components/experiments/StatusBadge'

const meta: Meta<typeof StatItem> = {
  component: StatItem,
  parameters: { layout: 'padded' },
  title: 'Components/Data Display/StatItem',
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

export const WithSub: Story = {
  args: {
    icon: 'bar-chart',
    label: 'Total API Calls',
    sub: 'of 2M plan limit',
    value: 1240000,
  },
}

export const WithBadge: Story = {
  args: {
    badge: <StatusBadge status='running' />,
    icon: 'flask',
    label: 'Experiment',
    sub: 'started 12 days ago',
    value: 'Checkout v2',
  },
}

// The icon is optional: dense rows of figures often read better without one.
export const WithoutIcon: Story = {
  args: {
    label: '% of plan consumed',
    sub: 'this billing period',
    value: '62%',
  },
}
